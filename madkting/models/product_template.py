# -*- coding: utf-8 -*-
# File:           product_template.py
# Author:         Israel Calderón
# Copyright:      (C) 2019 All rights reserved by Madkting
# Created:        2019-04-17

from odoo import models, api
from odoo import exceptions
from collections import defaultdict
from ..log.logger import logger
from ..responses import results
import psycopg2


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    @api.model
    def update_mapping_fields(self, product_data):
        product_data = self.env['yuju.mapping.field'].update_mapping_fields(product_data, 'product.template')
        return product_data

    @api.model
    def mdk_create(self, product_data, id_shop=None):
        """
        TODO: Prices are defined by product not variant. This behavior may be emulated with discount rules in odoo
              at this moment there is only price definition by product
        :param product_data:
        {
            'name': str,
            'default_code': str, # sku
            'type': str, # 'product', 'service', 'consu'
            'description': str,
            'description_purchase': str,
            'description_sale': str,
            'list_price': float,
            'company_id': int,
            'description_picking': str,
            'description_pickingout': str,
            'description_pickingin': str,
            'image': str, # base64 string
            'category_id': int,
            'taxes': list, # list of int
            'cost': float,
            'weight': float, # only if is parente product
            'weight_unit': str,
            'barcode': str, # only if is parent product
            'initial_stock': int, # TODO: implement initial stock functionality
            'variation_attributes': {
                'color':['blue', 'black'], # example variation
                'size': ['S', 'L'] # example variation
            }, # dict with variation as key and values in a list
            'variations': [
                {
                    'default_code': str,
                    'company_id': int,
                    'barcode': str,
                    'weight': float,
                    'cost': float,
                    'initial_stock': int, # TODO: implement initial stock functionality
                    'color': 'blue',
                    'size': 'S'
                }
            ]
        }
        :type product_data: dict
        :return:
        :rtype: dict
        """
        logger.debug("### MDK CREATE PRODUCT DATA ###")
        logger.debug(product_data)
        config = self.env['madkting.config'].get_config()
        mapping = self.env['yuju.mapping.product']
        products = self.env['product.product']

        if config and config.simple_description_enabled:
            try:
                product_data.pop('description_sale')
                product_data.pop('description_purchase')
                product_data.pop('description_picking')
                product_data.pop('description_pickingout')
                product_data.pop('description_pickingin')
            except Exception as e:
                logger.debug(e)
                pass

        is_multi_shop = False
        if product_data.get('is_multi_shop'):
            product_data.pop('is_multi_shop')
            is_multi_shop = True

        company_id = product_data.get('company_id', False)
        variation_attributes = product_data.pop('variation_attributes', None)
        variations = product_data.pop('variations', [])
        has_variations = True if variation_attributes else False
        taxes = product_data.pop('taxes', None)
        weight_unit = product_data.pop('weight_unit', None)
        if 'image' in product_data:
            product_data['image_1920'] = product_data.pop('image', None)
        # stock = product_data.pop('initial_stock', None)
        if taxes:
            taxes_id = self.env['account.tax'] \
                           .get_sale_taxes_ids(product_data['company_id'], taxes)
            product_data['taxes_id'] = taxes_id

        if weight_unit:
            weight_uom = self.env['uom.uom'].get_uom_by_name(weight_unit)
            product_data['weight_uom_name'] = weight_uom.name

        if product_data.get('cost'):
            product_data['standard_price'] = product_data.pop('cost', None)

        supplier_data = False
        if product_data.get('provider'):
            supplier_data = product_data.pop('provider', None)

        logger.debug("### SEARCH BARCODE : {} ###".format(product_data.get('barcode')))
        if 'barcode' in product_data:
            barcode = product_data.get('barcode')
            if barcode:
                
                product_ids = self.env['product.product'].with_context(active_test=False).search([('barcode', '=', barcode)])
                if product_ids.ids:
                    logger.warning(f'El codigo de barras ya esta previamente registrado {barcode}')

                    if config.validate_barcode_exists:               
                        return results.error_result(code='duplicated_barcode',
                                                description='El codigo de barras ya esta previamente registrado')
                    else:
                        product_data.pop('barcode')
            else:
                logger.debug("## DROP EMPTY BARCODE ##")
                product_data.pop('barcode')

        product_data = self.update_mapping_fields(product_data)

        # create a product simple
        if not has_variations:
            logger.debug("#CREATE PRODUCT SIMPLE")
            if id_shop:
                id_product_madkting = product_data.get('id_product_madkting')
                sku_product = product_data.get('default_code')
                product_mapping_data = {     
                    'product_id' : False, 
                    'id_product_yuju' : id_product_madkting,
                    'id_shop_yuju' : id_shop,
                    'default_code' : sku_product,
                    'state' : 'active'
                }
                product_ids = self.env['product.product'].search([('default_code', '=', sku_product)], limit=1)
                if product_ids:
                    product_mapping_data.update({'product_id' : product_ids.id})
                    try:
                        mapping.create_or_update_product_mapping(product_mapping_data)
                    except Exception as ex:
                        logger.exception(ex)
                        return results.error_result(code='product_create_error',
                                                    description='Product Mapping couldn\'t be created because '
                                                                'of the following exception: {}'.format(ex))

                else:
                    try:
                        new_product_simple = self.env['product.product'].create(product_data)
                    except Exception as ex:
                        logger.exception(ex)
                        return results.error_result(code='product_create_error',
                                                    description='Product couldn\'t be created because '
                                                                'of the following exception: {}'.format(ex))
                    else:
                        try:
                            product_mapping_data.update({'product_id' : new_product_simple.id})
                            mapping.create_or_update_product_mapping(product_mapping_data)
                        except Exception as ex:
                            logger.exception(ex)
                            """Si no se logra crear el mapeo, se elimina el producto que se acaba de crear"""
                            new_product_simple.unlink()
                            return results.error_result(code='product_create_error',
                                                        description='Product mapping couldn\'t be created because '
                                                                    'of the following exception: {}'.format(ex))
                        else:                        
                            # if stock:
                            #    pass # TODO: implement initial stock functionality
                            
                            if supplier_data:
                                new_product_simple._create_supplier_product(supplier_data)

                            return results.success_result(data=new_product_simple.get_data_with_variations())         
            else:
                try:
                    new_product_simple = self.env['product.product'].create(product_data)
                except Exception as ex:
                    logger.exception(ex)
                    return results.error_result(code='product_create_error',
                                                description='Product couldn\'t be created because '
                                                            'of the following exception: {}'.format(ex))
                else:
                    if supplier_data:
                        new_product_simple._create_supplier_product(supplier_data)

                    return results.success_result(data=new_product_simple.get_data_with_variations())

        # create product with variations
        # validate variations
        product_template_attribute_lines = []

        for attribute_name, values in variation_attributes.items():
            attribute_line = dict()
            attribute = self.env['product.attribute'].search([('name', '=', attribute_name)], limit=1)
            if not attribute:
                try:
                    # create attribute
                    attribute = self.env['product.attribute'].create({'name': attribute_name,
                                                                      'create_variant': 'always'})
                    # create new attribute values
                    self.env['product.attribute.value'].create(
                        [{'name': val, 'attribute_id': attribute.id} for val in values]
                    )
                except Exception as ex:
                    logger.exception(ex)
                    return results.error_result(code='create_variation_attribute_error',
                                                description='Product couldn\'t be created because '
                                                            'of the following exception: {}'.format(ex))
            else:
                current_attribute_values = {val.name: val.id for val in attribute.value_ids}
                _has_new_values_created = False
                for value in values:
                    if value not in current_attribute_values:
                        try:
                            new_att_val = self.env['product.attribute.value'].create({'name': value,
                                                                                      'attribute_id': attribute.id})
                        except Exception as ex:
                            logger.exception(ex)
                            return results.error_result(code='create_variation_attribute_value_error',
                                                        description='Product couldn\'t be created because '
                                                                    'of the following exception: {}'.format(ex))
                        else:
                            _has_new_values_created = True
                            current_attribute_values[new_att_val.name] = new_att_val.id
                if _has_new_values_created:
                    # if new values has been created for this attribute
                    # invalidate the cache in order to get value_ids updated
                    attribute.invalidate_cache()
            
            attribute_line = {
                'attribute_id': attribute.id,
                'value_ids': [
                    (4, val.id) for val in attribute.value_ids if val.name in values
                ]
            }
            product_template_attribute_lines.append((0, 0, attribute_line))

        product_data['attribute_line_ids'] = product_template_attribute_lines
        product_data.pop('id_product_madkting', None)

        logger.debug("#### VER VARIANTES")
        logger.debug(product_data)
        logger.debug(id_shop)
        
        if id_shop:
            new_template = None            
            sku_product = product_data.get('default_code')
            product_ids = products.search([('default_code', '=', sku_product)], limit=1)
            if product_ids:
                new_template = product_ids.product_templ_id
            else:
                for var in variations:
                    sku_product = var.get('default_code')
                    product_ids = products.search([('default_code', '=', sku_product)], limit=1)
                    if product_ids:
                        new_template = product_ids.product_tmpl_id
                        break

            if not new_template:
                try:
                    new_template = self.create(product_data)
                except Exception as ex:
                    logger.exception(ex)
                    return results.error_result(code='product_template_create_error',
                                                description='Product couldn\'t be created because '
                                                            'of the following exception: {}'.format(ex))
        else:
            try:
                new_template = self.create(product_data)
            except Exception as ex:
                logger.exception(ex)
                return results.error_result(code='product_template_create_error',
                                            description='Product couldn\'t be created because '
                                                        'of the following exception: {}'.format(ex))
        
        for product_variant in new_template.product_variant_ids:
            data = product_variant.get_data()

            variation_data = None
            for v in range(len(variations)):
                if all(attrib in variations[v] and variations[v][attrib] == value for attrib, value in data.get('attributes').items() ):
                    variation_data = variations.pop(v)
                    break
            logger.debug("## VARIATION DATA ##")
            logger.debug(variation_data)
            if variation_data:
                logger.debug("Entra..")
                if variation_data.get('cost'):
                    variation_data['standard_price'] = variation_data.pop('cost', None)

                if 'image' in variation_data:
                    variation_data['image_1920'] = variation_data.pop('image', None)

                if supplier_data:
                    product_variant._create_supplier_product(supplier_data)

                for attrib in data.get('attributes'):
                    variation_data.pop(attrib)

                variation_data.pop('attributes', None)
                variation_data.pop('product_id', None)
                variation_data.pop('id', None)

                if id_shop:
                    is_multi_shop = False
                    if variation_data.get('is_multi_shop'):
                        variation_data.pop('is_multi_shop')
                        is_multi_shop = True
                        
                    id_product_madkting = variation_data.get('id_product_madkting')
                    sku_variant = variation_data.get('default_code')
                    variant_mapping_data = {     
                        'product_id' : product_variant.id,
                        'id_product_yuju' : id_product_madkting,
                        'id_shop_yuju' : id_shop,
                        'default_code' : sku_variant,
                        'state' : 'active'
                    }                                               
                    try:
                        mapping.create_or_update_product_mapping(variant_mapping_data)
                    except Exception as ex:
                        logger.exception(ex)
                        return results.error_result(code='product_create_error',
                                                description='Product mapping couldn\'t be created because '
                                                            'of the following exception: {}'.format(ex))
                
                logger.debug("## VARIATION DATA ##")
                logger.debug(variation_data)
                product_variant.write(variation_data)

        return results.success_result(new_template.product_variant_id.get_data_with_variations())

    def change_product_status(self, template_id, active, id_shop=None):
        """
        :param template_id:
        :type template_id: int
        :param active:
        :type active: bool
        :return:
        :rtype: dict
        """
        product = self.with_context(active_test=False) \
                      .search([('id', '=', template_id)], limit=1)
        if not product:
            return results.error_result(
                'product_not_found',
                'The product that you are trying to change doesn\'t exists or has been deleted'
            )
        try:
            if id_shop:
                yuju_mapping = self.env['yuju.mapping'].sudo()
                product_mapping = self.env['yuju.mapping.product'].sudo()
                mapping = yuju_mapping.search([('id_shop_yuju', '=', id_shop)])
                if not mapping.ids:
                    return results.error_result(
                        'product_not_found',
                        'Mapping record not found for id_shop {} in activate/deactivate'.format(id_shop)
                    )
                mapping_state = 'active' if active else 'disabled'
                update_template = True
                for variation in product.product_variant_ids:
                    if update_template:
                        mapping_product = product_mapping.get_product_mapping_by_product(variation.id, only_active=True)
                        if mapping_product and len(mapping_product.ids) > 1:
                            update_template = False

                if update_template:
                    for variation in product.product_variant_ids:
                        mapping_product = self.env['yuju.mapping.product'].sudo().search([('product_id', '=', variation.id), ('id_shop_yuju', '=', id_shop)], limit=1)
                        if mapping_product.ids:
                            mapping_product.write({'state' : mapping_state})                            
                    product.active = active                
                else:
                    for variation in product.product_variant_ids:
                        mapping_product = self.env['yuju.mapping.product'].sudo().search([('product_id', '=', variation.id), ('id_shop_yuju', '=', id_shop)], limit=1)
                        if mapping_product.ids:
                            mapping_product.write({'state' : mapping_state})

            else:
                product.active = active
        except Exception as ex:
            logger.exception(ex)
            return results.error_result('activate_product_error', str(ex))
        else:
            return results.success_result(
                product.product_variant_id.get_data_with_variations()
            )

    @api.model
    def deactivate_product(self, template_id, id_shop=None):
        """
        :param template_id:
        :type template_id: int
        :return:
        """
        """
        variant deactivation may bring adverse results,
        you should validate the default odoo behavior before allow this functionality
        """
        return self.change_product_status(template_id, active=False, id_shop=id_shop)

    @api.model
    def activate_product(self, template_id, id_shop=None):
        """
        :param template_id:
        :type template_id: int
        :return:
        """
        return self.change_product_status(template_id, active=True, id_shop=id_shop)

    @api.model
    def delete_product(self, template_id, id_shop=None):
        """
        :param template_id:
        :type template_id: int
        :rtype: dict
        :return:
        """
        product = self.search([('id', '=', template_id)])
        if not product:

            # product = self.with_context(active_test=False) \
            #     .search([('id', '=', template_id)])

            return results.success_result()
            # return results.error_result(
            #     'product_not_found',
            #     'The product that you are trying to delete doesn\'t exists or is deleted already'
            # )
        try:
            if id_shop:
                yuju_mapping = self.env['yuju.mapping'].sudo()
                product_mapping = self.env['yuju.mapping.product'].sudo()
                mapping = yuju_mapping.search([('id_shop_yuju', '=', id_shop)])
                if not mapping.ids:
                    return results.error_result(
                        'product_not_found',
                        'Mapping record not found for id_shop {}'.format(id_shop)
                    )
                delete_template = True
                for variation in product.product_variant_ids:
                    if delete_template:
                        mapping_product = product_mapping.get_product_mapping_by_product(variation.id)
                        if mapping_product and len(mapping_product.ids) > 1:
                            delete_template = False
                if delete_template:
                    product.unlink() 
                else:
                    for variation in product.product_variant_ids:         
                        mapping_product = product_mapping.get_product_mapping(variation.id, id_shop)
                        if mapping_product:
                            mapping_product.unlink()
                               
            else:
                product.unlink()
        except (exceptions.ValidationError, psycopg2.IntegrityError) as ve:
            logger.exception(ve)
            return results.error_result(
                'related_with_sales',
                'The product cannot be deleted because is related with sale orders'
            )
        except Exception as ex:
            logger.exception(ex)
            return results.error_result('delete_product_exception', str(ex))
        else:
            return results.success_result()
