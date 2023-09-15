# -*- coding: utf-8 -*-
# File:           res_partner.py
# Author:         Israel Calderón
# Copyright:      (C) 2019 All rights reserved by Madkting
# Created:        2019-07-19

from odoo import models, api, fields
from odoo import exceptions


from ..responses import results
from ..log.logger import logger

from ..notifier import notifier

from collections import defaultdict
import math

class ProductProduct(models.Model):
    _inherit = "product.product"

    id_product_madkting = fields.Char('Id product madkting', size=50)
    tipo_producto_yuju = fields.Selection([('dropship', 'Dropship'), ('mto', 'MTO')],
                                            string='Tipo Ruta Producto', 
                                            help='En caso de no tener stock como se procesará Yuju el pedido para este producto, \n'
                                                 'Dropship: Lo surte el proveedor \n' 
                                                 'MTO: Se compra y lo surte la empresa')

    _sql_constraints = [('id_product_madkting_uniq', 'unique (id_product_madkting,active)',
                         'The relationship between products of madkting and odoo must be one to one!')]

    __update_product_fields = {'name': str,
                               'default_code': str,
                               'type': str,  # 'product', 'service', 'consu'
                               'description': str,
                               'description_purchase': str,
                               'description_sale': str,
                               'list_price': (int, float),
                               'company_id': int,
                               'description_picking': str,
                               'description_pickingout': str,
                               'description_pickingin': str,
                               'image': str,
                               'category_id': int,
                               'taxes': list,
                               'standard_price': (float, int),
                               'weight': (float, int),
                               'weight_unit': str,
                               'barcode': str,
                               'id_product_madkting': (int, str)}

    __update_variation_fields = {'default_code': str,
                                 'company_id': int,
                                 'standard_price': (float, int),
                                 'attributes': dict,
                                 'type' : str,
                                 'detailed_type' : str,
                                 'id_product_madkting': (int, str)}

    def show_qty(self):
        qty_available = self.with_context({'location' : 8}).qty_available
        free_qty = self.with_context({'location' : 8}).free_qty
        post_message = f"Qty {qty_available}."
        post_message2 = f"Free Qty {free_qty}."
        logger.info(f"## QTY IN BRANCH: {post_message}")
        logger.info(f"## QTY IN BRANCH: {post_message2}")

    def send_webhook(self):
        """
        :param product_id:
        :type product_id: int
        :return:
        :rtype: dict
        """        
        for product in self:
            if not product.id_product_madkting:
                product.message_post(body="Error al lanzar webhook: El producto no esta mapeado con Yuju")
                return
            if not product.company_id:
                company_id = self.env.user.company_id.id
            else:
                company_id = product.company_id.id
            try:
                notifier.send_stock_webhook(self.env, product, company_id)
            except Exception as ex:
                logger.debug("###Exception Ocurred on Sending Webhook")
                logger.debug(ex)        
                
        return results.success_result()

    @api.model
    def send_webhook_all(self, company_id):
        """
        :param product_id:
        :type product_id: int
        :return:
        :rtype: dict
        """        
        product_ids = self.search([('id_product_madkting', '!=', False)])

        if not product_ids:
            return results.error_result('product_not_found',
                                        'product_id not found')

        for product in product_ids:
            try:
                notifier.send_stock_webhook(self.env, product, company_id)
            except Exception as ex:
                logger.debug("###Exception Ocurred on Sending Webhook")
                logger.debug(ex)        
            
        return results.success_result()
    
    @api.model
    def get_stock_data(self, location_id):
        config = self.env['madkting.config'].get_config()
        product_ids = self.search([('id_product_madkting', '!=', False)])
        product_data = []
        if config.stock_source_multi:
            for product in product_ids:
                stock_product = 0
                for location in config.stock_source_multi.split(','):
                    location_id = int(location)
                    qty_in_branch = product.with_context({"location" : location_id}).free_qty
                    stock_product += qty_in_branch
                product_data.append({
                    "product_id" : str(product.id_product_madkting),
                    "sku" : product.default_code,
                    "price" : product.lst_price,
                    "stock" : stock_product
                })                
        
        logger.debug("## STOCK DATA ##")
        logger.debug(product_data)
        # response = {"data" : [product_data]}
        return results.success_result(product_data)

    @api.model
    def send_webhook_by_id_product_madkting(self, id_product_madkting, company_id):
        """
        :param id_product_madkting:
        :type id_product_madkting: int
        :return:
        :rtype: dict
        """
        product_ids = self.search([('id_product_madkting', '=', id_product_madkting)])

        if not product_ids:
            return results.error_result('product_not_found',
                                        'product_id not found')

        for product in product_ids:
            try:
                notifier.send_stock_webhook(self.env, product.id, company_id)
            except Exception as ex:
                logger.debug("###Exception Ocurred on Sending Webhook")
                logger.debug(ex)        
            
        return results.success_result()

    @api.model
    def _create_supplier_product(self, supplier_data):  
        logger.debug("## CREATE SUPPLIER PRODUCT ##")      
        try:
            supplier_id = self.env['res.partner'].search(['|', ('email', '=', supplier_data.get('email')), ('vat', '=', supplier_data.get('rfc'))], limit=1)
            logger.debug(supplier_id)
            if not supplier_id.id:
                logger.debug("## Supplier not exists ##")
                supplier_id = self.env['res.partner'].create({
                    "name" : supplier_data.get('name'),
                    "phone" : supplier_data.get('contact'),
                    "email" : supplier_data.get('email'),
                    "vat" : supplier_data.get('rfc'),
                })
        except Exception as e:
            # No se pudo crear el proveedor
            logger.exception(e)
            pass
        else:
            logger.debug("## ELSE ##")
            try:
                logger.debug(self)
                logger.debug(self.seller_ids)
                if not self.seller_ids:
                    self.write({
                        "seller_ids" : [(0, 0, {
                            "name" : supplier_id.id,
                            "product_uom" : 1,
                            "price" : supplier_data.get('cost', 1)
                        })]
                    })
            except Exception as e:
                logger.exception(e)
                pass

    @api.model
    def update_mapping_fields(self, product_data):
        product_data = self.env['yuju.mapping.field'].update_mapping_fields(product_data, 'product.product')
        return product_data

    @api.model
    def update_product(self, product_data, product_type, id_shop=None):
        """
        :param product_data:
        :type product_data: dict
        :param product_type: type of the product being updated: 'product' or 'variation'
        :type product_type: str
        :return:
        :rtype: dict
        """
        logger.debug("### UPDATE PRODUCT ###")
        logger.debug(product_data)
        logger.debug(id_shop)
        product_id = product_data.pop('id', None)
        if not product_id:
            return results.error_result('missing_product_id',
                                        'product_id is required')

        product = self.with_context(active_test=False) \
                      .search([('id', '=', product_id)])
        if not product:
            return results.error_result('product_not_found',
                                        'The product you are looking for does not exists in odoo or has been deleted')
        
        config = self.env['madkting.config'].get_config()

        supplier_data = False
        if product_data.get('provider'):
            supplier_data = product_data.pop('provider')
            product._create_supplier_product(supplier_data)

        fields_validation = self.__validate_update_fields(fields=product_data,
                                                          product_type=product_type)
        if not fields_validation['success']:
            logger.debug(fields_validation)
            return fields_validation

        is_mapping = False
        if product_data.get('is_mapping'):
            product_data.pop('is_mapping')
            is_mapping = True
        
        is_multi_shop = False
        if product_data.get('is_multi_shop'):
            product_data.pop('is_multi_shop')
            is_multi_shop = True

        if id_shop:
            mapping = self.env['yuju.mapping.product']
            id_product_madkting = product_data.get('id_product_madkting')
            default_code = product_data.get('default_code')
            mapping_data = {     
                'product_id' : int(product_id),
                'id_product_yuju' : id_product_madkting,
                'id_shop_yuju' : id_shop,
                'default_code' : default_code,
                'state' : 'active'
            }

            if not is_mapping and product.product_tmpl_id.attribute_line_ids and not product_data.get('attributes'):
                logger.debug("Product Template related not update mapping in multi shop")
            else:
                try:
                    mapping.create_or_update_product_mapping(mapping_data)
                except Exception as ex:
                    logger.exception(ex)
                    return results.error_result(code='save_product_update_exception',
                                                description='Product mapping couldn\'t be created because '
                                                            'of the following exception: {}'.format(ex))

        # if 'l10n_mx_edi_code_sat_id' in fields_validation['data']:
        #     sat_code = fields_validation['data']['l10n_mx_edi_code_sat_id']
        #     sat_code_ids = self.env['l10n_mx_edi.product.sat.code'].search([('code', '=', sat_code)], limit=1)
        #     if sat_code_ids:
        #         fields_validation['data']['l10n_mx_edi_code_sat_id'] = sat_code_ids[0].id
        #     else:
        #         fields_validation.pop('l10n_mx_edi_code_sat_id')
        #         fields_validation['data'].pop('l10n_mx_edi_code_sat_id')

        fields_validation['data'] = self.update_mapping_fields(fields_validation['data'])

        if 'image' in fields_validation['data']:
            fields_validation['data']['image_1920'] = fields_validation['data'].pop('image', None)

        fields_validation.pop('attributes', None)
        fields_validation['data'].pop('attributes', None)

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
        
        related_skus = []
        related_ids = []
        
        parent = product.product_tmpl_id
        for pv in parent.product_variant_ids:
            related_skus.append(pv.default_code)
            related_ids.append(pv.id_product_madkting)

        logger.debug("Related Skus")
        logger.debug(related_skus)

        logger.debug("Related Ids")
        logger.debug(related_ids)

        updatable_sku = fields_validation['data'].get('default_code')
        id_yuju = fields_validation['data'].get('id_product_madkting')

        is_related = False if updatable_sku not in related_skus and id_yuju not in related_ids else True

        logger.debug("Is Related")
        logger.debug(is_related)
        
        # Se quita el default code de la actualizacion, agreado en multi shop, este campo no es editable desde yuju 
        # ya que una vez asignado no puede modificarse
        if 'default_code' in fields_validation['data']:
            
            if product.default_code:
                
                if fields_validation['data'].get('default_code') != product.default_code:
                    if config.validate_sku_exists and not is_related:
                        logger.warning(f"Trying to update a different sku product, ignore product_id: {product_id}, default_code: {updatable_sku}, id_yuju: {id_yuju}")
                        return results.success_result()
                    # return results.error_result(code='different_sku',
                    #                                 description='El sku del producto mapeado es distinto')

                fields_validation['data'].pop('default_code')
            # else:
            #     if config.validate_sku_exists:
            #         default_code = fields_validation['data'].get('default_code')
            #         product_ids = self.sudo().search([('default_code', '=', default_code), ('id', '!=', product_id)], limit=1)
            #         if product_ids.ids:
            #             return results.error_result(code='duplicated_sku',
            #                                             description='El SKU ya esta previamente registrado')

        # Si el producto cuenta actualmente con un id_product_madkting, el mapeo ya esta hecho y no debe sobre-escribirse
        # En caso de querer hacer el mapeo, debe eliminarse por script o manualmente el id_product_madkting del registro
        # Esto permitira que las nuevas tiendas mapeadas a este mismo producto no reemplacen la referencia original y 
        # se manejen por la tabla de mapeo al enviar el webhoook 
        if 'id_product_madkting' in fields_validation['data']:

            if product.id_product_madkting:
                
                if str(fields_validation['data'].get('id_product_madkting')) != str(product.id_product_madkting):
                    if config.validate_id_exists and not is_related:
                        logger.warning(f"Trying to update a different id product, ignore product_id: {product_id}, default_code: {updatable_sku}, id_yuju: {id_yuju}")
                        return results.success_result()
                
                fields_validation['data'].pop('id_product_madkting')
            # else:
            #     if config.validate_id_exists:
            #         id_product_madkting = fields_validation['data'].get('id_product_madkting')
            #         product_ids = self.sudo().search([('id_product_madkting', '=', id_product_madkting), ('id', '!=', product_id)], limit=1)
            #         if product_ids.ids:
            #             return results.error_result(code='duplicated_id_product',
            #                                         description='El id producto ya esta previamente mapeado')

            

        # Si se realiza un mapeo a un catalogo que ya esta mapeado actualmente, el formulario tendra el campo company_id
        # con un valor establecido, lo cual para efectos del modulo multi shop, el catalogo de productos sera compartido
        # por lo que el campo company_id se establecera como False
        if is_multi_shop and config.product_shared_catalog_enabled and product.company_id:
            fields_validation['data']['company_id'] = False
        
        logger.debug("#### DATA TO WRITE ####")
        logger.debug(fields_validation['data'])

        if "barcode" in fields_validation["data"]: 
            barcode = fields_validation["data"]["barcode"]
            if barcode == "":
                # Drop empty barcode because constraint product_product_barcode_uniq
                fields_validation["data"].pop("barcode")
                logger.debug("Pop barcode..")
            else:
                logger.debug("## SEARCH BARCODE UPDATE ##")
                product_ids = self.with_context(active_test=False).search([('barcode', '=', barcode), ('id', '!=', product_id)])
                if product_ids.ids:
                    logger.warning(f'El codigo de barras ya esta previamente registrado {barcode}')

                    if config.validate_barcode_exists:               
                        return results.error_result(code='duplicated_barcode',
                                                description='El codigo de barras ya esta previamente registrado')
                    else:
                        fields_validation["data"].pop("barcode")

        logger.debug("## Fields validation data")
        logger.debug(fields_validation['data'])
        try:
            product.write(fields_validation['data'])
            # if config and config.update_parent_list_price and fields_validation['data'].get('list_price'):
            #     logger.debug("## UPDATE PARENT PRICE {}##".format(product.product_tmpl_id))
            #     product_list_price = fields_validation['data'].get('list_price')
            #     product.product_tmpl_id.write({"list_price" : product_list_price})

        except exceptions.AccessError as ae:
            logger.exception(ae)
            return results.error_result('access_error', ae)
        except Exception as ex:
            logger.exception(ex)
            logger.debug("AQUI")
            return results.error_result('save_product_update_exception', ex)
        else:
            return results.success_result()

    @api.model
    def create_variation(self, variation_data, id_shop=None):
        """
        :param variation_data:
        {
            'product_id': int, # parent product id
            'default_code': str,
            'company_id': int,
            'standard_price': float,
            'attributes': { # example variation attributes
                'color': 'blue',
                'size': 'S'
            }
        }
        :type variation_data: dict
        :return:
        :rtype: dict
        """
        logger.debug("### CREATE VARIATION ###")
        logger.debug(variation_data)
        config = self.env['madkting.config'].get_config()
        parent_id = variation_data.pop('product_id', None)
        if not parent_id:
            return results.error_result('missing_product_id',
                                        'product_id is required')

        parent = self.search([('id', '=', parent_id)])
        if not parent:
            return results.error_result(
                'product_not_found',
                'Cannot find the parent product for this variation'
            )
        if variation_data.get('cost'):
            variation_data['standard_price'] = variation_data.pop('cost', None)
        fields_validation = self.__validate_update_fields(variation_data,
                                                          'variation')
        if not fields_validation['success']:
            return fields_validation

        logger.debug("## Fields validation")
        logger.debug(fields_validation)

        if "barcode" in variation_data: 
            barcode = variation_data.get("barcode")
            if barcode == "":
                # Drop empty barcode because constraint product_product_barcode_uniq
                variation_data.pop("barcode")
                logger.debug("Pop barcode..")
            else:
                logger.debug("## SEARCH BARCODE UPDATE ##")
                product_ids = self.with_context(active_test=False).search([('barcode', '=', barcode)])
                if product_ids.ids:
                    logger.warning(f'El codigo de barras ya esta previamente registrado {barcode}')

                    if config.validate_barcode_exists:               
                        return results.error_result(code='duplicated_barcode',
                                                description='El codigo de barras ya esta previamente registrado')
                    else:
                        variation_data.pop("barcode")        

        attributes_structure = parent.attribute_lines_structure()
        variant_attributes = fields_validation['data'].pop('attributes')
        invalid_attributes = list()
        attribute_values = set()

        if 'image' in fields_validation['data']:
            fields_validation['data']['image_1920'] = fields_validation['data'].pop('image', None)

        for attribute, value in variant_attributes.items():
            attribute_values.add(value)
            if attribute not in attributes_structure:
                invalid_attributes.append(attribute)

        if invalid_attributes:
            return results.error_result(
                'invalid_variation_structure',
                '{} doesn\'t match variation structure'.format(', '.join(invalid_attributes))
            )

        current_variations_set = parent.get_variation_sets()
        v_data = fields_validation['data']
        logger.debug("## Current variation set")
        logger.debug(current_variations_set)

        logger.debug("## V Data")
        logger.debug(v_data)

        logger.debug("## Attribute values")
        logger.debug(attribute_values)

        logger.debug("## Variant Attribute")
        logger.debug(variant_attributes)

        mapping = self.env['yuju.mapping.product']

        if attribute_values in current_variations_set:
            for variation in parent.product_variant_ids:

                logger.debug("## Variant Data Attributes #1 ")
                logger.debug(variation.get_data().get('attributes'))

                if variant_attributes == variation.get_data().get('attributes'):                    
                    if id_shop:
                        id_product_madkting = v_data.get('id_product_madkting')
                        default_code = v_data.get('default_code')
                        mapping_data = {
                            'product_id' : variation.id,
                            'id_product_yuju' : id_product_madkting,
                            'id_shop_yuju' : id_shop,
                            'default_code' : default_code,
                            'state' : 'active'
                        }
                        try:
                            mapping.create_or_update_product_mapping(mapping_data)
                        except Exception as ex:
                            logger.exception(ex)
                            return results.error_result(code='save_product_update_exception',
                                                        description='Product mapping couldn\'t be created because '
                                                                    'of the following exception: {}'.format(ex))
                            
                    variation.write(fields_validation['data'])
                    return results.success_result(variation.get_data())

        new_variation_values_ids = list()
        new_attribute_lines = []
        for attribute, value in variant_attributes.items():
            # logger.in0fo(attributes_structure)
            value_id = attributes_structure[attribute].get('values').get(value)
            # logger.debug(value_id)
            # if this value_id is not already assigned to this attribute line
            if not value_id:
                # try to get value from the existing attribute
                attribute_id = attributes_structure[attribute]['attribute_id']
                attribute_val = self.env['product.attribute.value'] \
                                    .search([('attribute_id', '=', attribute_id), ('name', '=', value)],
                                            limit=1)
                if not attribute_val:
                    # if the attribute value doesn't exists yet create it
                    try:
                        attribute_val = self.env['product.attribute.value'].create(
                            {'name': value, 'attribute_id': attribute_id}
                        )
                    except Exception as ex:
                        logger.exception(ex)
                        return results.error_result(
                            'create_variation_attribute_value_error',
                            str(ex)
                        )
                    else:
                        template_attribute_line_id = attributes_structure[attribute]['attribute_line_id']
                        attribute_line = self.env['product.template.attribute.line'].browse(template_attribute_line_id)
                        try:
                            # add new value to product template attribute line
                            attribute_line.value_ids = [(4, attribute_val.id)]
                        except Exception as ex:
                            logger.exception(ex)

                new_attribute_lines.append({
                    'attribute_line_id': attributes_structure[attribute].get('attribute_line_id'),
                    'value_id': attribute_val.id
                })
                
        attribute_line_ids = [
                (1, a['attribute_line_id'], {'value_ids': [(4, a['value_id'])]}) for a in new_attribute_lines
        ]
        logger.debug("## Attribute line ids")
        logger.debug(attribute_line_ids)
        try:
            parent.product_tmpl_id.write({'attribute_line_ids': attribute_line_ids})
        except Exception as ex:
            logger.exception(ex)
            return results.error_result('variation_create_error', str(ex))

        new_variation_data = None
        v_data = fields_validation['data']

        logger.debug("## New variation data 222")
        logger.debug(new_variation_data)

        logger.debug("## V data")
        logger.debug(v_data)

        for variation in parent.product_variant_ids:
            logger.debug("## Variant Data Attributes #2 ")
            logger.debug(variation.get_data().get('attributes'))
            if variant_attributes == variation.get_data().get('attributes'):
                # logger.debug(fields_validation['data'])
                if id_shop:
                    id_product_madkting = v_data.get('id_product_madkting')
                    default_code = v_data.get('default_code')
                    mapping_data = {
                        'product_id' : variation.id,
                        'id_product_yuju' : id_product_madkting,
                        'id_shop_yuju' : id_shop,
                        'default_code' : default_code,
                        'state' : 'active'
                    }
                    try:
                        mapping.create_or_update_product_mapping(mapping_data)
                    except Exception as ex:
                        logger.exception(ex)
                        return results.error_result(code='save_product_update_exception',
                                                    description='Product mapping couldn\'t be created because '
                                                                'of the following exception: {}'.format(ex))
                       
                variation.write(fields_validation['data'])
                new_variation_data = variation.get_data()
                break

        if not new_variation_data:
            return results.error_result('new_variation_missing', 'The variation was created couldn\'t find it')

        return results.success_result(new_variation_data)

    @api.model
    def get_product(self, product_id, only_active=False, id_shop=None):
        """
        :param only_active:
        :type only_active: bool
        :param product_id:
        :type product_id: int
        :return:
        :rtype: dict
        """
        if not product_id:
            return results.error_result(
                'product_not_given',
                'The product id is null, it should be an integer'
            )

        product = self.with_context(active_test=only_active) \
                      .search([('id', '=', product_id)], limit=1)

        if not product:
            return results.error_result(
                'product_not_found',
                'The product that you are trying to get doesn\'t exists or has been deleted'
            )
        return results.success_result(product.get_data_with_variations())

    @api.model
    def get_variation(self, product_id, only_active=False, id_shop=None):
        """
        :param only_active:
        :type only_active: bool
        :param product_id:
        :type product_id: int
        :return:
        :rtype: dict
        """
        product = self.with_context(active_test=only_active) \
                      .search([('id', '=', product_id)], limit=1)

        if not product:
            return results.error_result(
                'product_not_found',
                'The product that you are trying to deactivate doesn\'t exists or has been deleted'
            )
        return results.success_result(product.get_data())

    @api.model
    def get_product_list(self, elements_per_page=50, page=1, id_shop=None):
        """
        :param elements_per_page: max 300
        :type elements_per_page: int
        :param page:
        :type page: int
        :return:
        :rtype: dict
        """
        if elements_per_page > 300:
            elements_per_page = 300

        if page < 1:
            page = 1

        products_total = self.search_count([])
        offset = elements_per_page * (page - 1)
        products = self.search([],
                               limit=elements_per_page,
                               offset=offset,
                               order='id asc')
        product_list = {
            'page_count': math.ceil(products_total / elements_per_page),
            'page': page,
            'products_total': products_total,
            'products': []
        }

        for product in products:
            product_list['products'].append({
                'id': product.id,
                'product_id': product.product_variant_id.id,
                'default_code': product.default_code,
                'categ_id': product.categ_id.id,
                'categ_name': product.categ_id.name
            })
        return results.success_result(product_list)

    @api.model
    def product_count(self, id_shop=None):
        """
        :return:
        """
        return results.success_result(self.search_count([]))

    @api.model
    def deindex_products(self, product_ids, id_shop=None):
        """
        :param product_ids:
        :type product_ids: list
        :return:
        """
        try:
            if product_ids[0] == '*':
                self.search([]).write({'id_product_madkting': None})
            else:
                self.search([('id', 'in', product_ids)]) \
                    .write({'id_product_madkting': None})
        except Exception as ex:
            logger.exception(ex)
            results.error_result('deindex_write_exception', str(ex))
        else:
            return results.success_result()

    def get_data(self):
        """
        :rtype: dict
        :return:
        """
        self.ensure_one()
        data = self.copy_data()[0]
        data['id'] = self.id
        data['product_id'] = self.product_variant_id.id
        data['template_id'] = self.product_tmpl_id.id
        data['standard_price'] = self.standard_price
        data['attributes'] = dict()
        for attribute_value in self.product_template_attribute_value_ids:
            attribute_name = attribute_value.attribute_id.name
            data['attributes'][attribute_name] = attribute_value.name
        return data

    def get_data_with_variations(self):
        """
        :rtype: dict
        :return:
        """
        self.ensure_one()
        data = self.product_tmpl_id.copy_data()[0]
        data['variations'] = list()
        variation_attributes = defaultdict(list)
        data['template_id'] = self.product_tmpl_id.id
        data['id'] = self.id
        data['default_code'] = self.default_code
        data['product_variant_count'] = self.product_tmpl_id.product_variant_count
        for variation in self.product_variant_ids:
            variation_data = variation.get_data()
            for attribute, value in variation_data['attributes'].items():
                if value not in variation_attributes[attribute]:
                    variation_attributes[attribute].append(value)
            data['variations'].append(variation_data)
        data['variation_attributes'] = dict(variation_attributes)
        return data

    def __validate_update_fields(self, fields, product_type):
        """
        :param fields:
        :param product_type:
        :return: results dict with updatable fields filtered and fields analysis results
        :rtype: dict
        """
        invalid_types = list()
        filtered_fields = dict()

        config = self.env['madkting.config'].get_config()

        if product_type == 'product':
            updatable_fields = self.__update_product_fields
            
            if config.product_custom_fields:
                for field in config.product_custom_fields.split(','):
                    updatable_fields.update({field : str})

        else:
            updatable_fields = self.__update_variation_fields

            # if config and config.update_parent_list_price:
            #     updatable_fields.update({'list_price': (int, float)})

        for field, value in fields.items():
            if field in updatable_fields:
                field_type = updatable_fields[field]
                if not isinstance(value, field_type):
                    invalid_types.append(field)
                else:
                    filtered_fields[field] = value

        if not fields:
            return results.error_result('nothing_to_update')

        if invalid_types:
            return results.error_result('invalid_field_type',
                                        ', '.join(invalid_types))
        return results.success_result(filtered_fields)

    def attribute_lines_structure(self):
        """
        :return: dictionary with attribute lines structure
        {
          'attribute name': {
            'attribute_id': int,
            'values': {
              'value name': value id,
              'value name': value id,
              ...
            },
            ...
          }
        :rtype: dict
        """
        self.ensure_one()
        structure = defaultdict(dict)
        for attribute_line in self.attribute_line_ids:
            attribute_name = attribute_line.attribute_id.name
            structure[attribute_name]['attribute_line_id'] = attribute_line.id
            structure[attribute_name]['attribute_id'] = attribute_line.attribute_id.id
            structure[attribute_name]['values'] = dict()
            for value in attribute_line.value_ids:
                structure[attribute_name]['values'][value.name] = value.id
        return dict(structure)

    def get_variation_sets(self):
        """
        :return: list of variations in sets
        :rtype: list
        """
        self.ensure_one()
        variants = list()
        for variation in self.product_variant_ids:
            values = set()
            for value in variation.product_template_attribute_value_ids:
                values.add(value.name)
            if values:
                variants.append(values)
        return variants

    def get_stock_by_location(self):
        """
        Returns the stock by location, only active locations of type internal
        :return:
        :rtype: dict
        """
        self.ensure_one()
        quantities = dict()
        locations = self.env['stock.location'] \
                        .search([('active', '=', True),
                                 ('usage', '=', 'internal')])
        for location in locations:
            quantities[location.id] = self.with_context({'location': location.id}) \
                                          .qty_available
        return quantities
