# -*- coding: utf-8 -*-
# File:           res_partner.py
# Author:         Israel Calderón
# Copyright:      (C) 2019 All rights reserved by Madkting
# Created:        2019-07-19

from odoo import models, api, fields
from odoo import exceptions
from odoo.exceptions import ValidationError

from ..responses import results
from ..log.logger import logger

from collections import defaultdict
import math

class YujuMapping(models.Model):
    _name = 'yuju.mapping'
    _description = 'Mapeo de Tiendas Yuju'

    company_id = fields.Many2one('res.company', 'Company')
    id_shop_yuju = fields.Char('Id Shop Yuju', size=50)

    _sql_constraints = [
        ('mapping_yuju_unique', 'unique(id_shop_yuju, company_id)', 'El mappeo ya existe')
    ]

    def get_mapping(self, company_id):
        mapping_ids = self.search_count([('company_id', '=', company_id)])
        if mapping_ids == 0:
            return False
        return self.search([('company_id', '=', company_id)])

    @api.model
    def create_mapping(self, mapping):            
        """
        The mapping table is limited to only one record per id_shop, company_id
        :param mapping:
        :type mapping: dict
        :return:
        """
        create_data = []
        mapping_created = []
        for m in mapping:
            company_id = m.get('company_id')
            company_ids = self.env['res.company'].search([('id', '=', int(company_id))], limit=1)
            if not company_ids:
                return results.error_result('The company {} not exists'.format(company_id))
            if not m.get('id_shop'):
                return results.error_result('The id shop is empty for company {}'.format(company_id))

            create_data = {
                "company_id" : company_ids.id,
                "id_shop_yuju" : m.get('id_shop')
            }

            try:
                new_row_id = self.create(create_data)
            except Exception as e:
                return results.error_result('Ocurrio un error al crear el mapeo', str(e))
            else:
                mapping_created.append(new_row_id.id)

        return results.success_result({'mapped_rows' : mapping_created})
       
class ProductYujuMapping(models.Model):
    _name = "yuju.mapping.product"
    _description = 'Mapeo de Productos Yuju'

    product_id = fields.Many2one('product.product', string='Product', ondelete='cascade')
    id_product_yuju = fields.Char('Id Product Yuju', size=50)
    id_shop_yuju = fields.Char('Id Shop Yuju')
    state = fields.Selection([('active', 'Activo'), ('disabled', 'Pausado')], 'Estatus')
    default_code = fields.Char('SKU')
    # company_id = fields.Many2one('res.company', 'Company')
    # barcode = fields.Char('Codigo de Barras')
    
    # _sql_constraints = [('id_product_mapping_uniq', 'unique (product_id, company_id, id_product_yuju, id_shop_yuju)',
    #                      'The relationship between products of yuju and odoo must be one to one!')]

    def create_or_update_product_mapping(self, mapping_data):
        logger.debug("#### CREATE MAPPING ###")
        logger.debug(mapping_data)
        product_id = mapping_data.get('product_id')
        id_shop = mapping_data.get('id_shop_yuju')
        mapping_ids = self.get_product_mapping(product_id, id_shop)
        if mapping_ids:
            try:
                mapping_ids.write(mapping_data)                
            except Exception as err:
                logger.exception(err)
                raise ValidationError('Error al actualizar el mapeo')
        else:
            try:
                self.create(mapping_data)
            except Exception as err:
                logger.exception(err)
                raise ValidationError('Error al crear el mapeo')
        return True

    def get_product_mapping(self, product_id, id_shop):
        logger.debug("#### GET MAPPING ###")
        mapping_ids = []
        count_mapping = self.search_count([('product_id', '=', int(product_id)), ('id_shop_yuju', '=', id_shop)])
        if count_mapping > 0:
            mapping_ids = self.search([('product_id', '=', int(product_id)), ('id_shop_yuju', '=', id_shop)], limit=1)
        logger.debug(mapping_ids)
        return mapping_ids

    def get_product_mapping_by_company(self, product_id, company_id):
        logger.debug("#### GET MAPPING ###")
        # logger.debug(product_id)
        # logger.debug(type(product_id))
        # logger.debug(id_shop)
        # logger.debug(type(id_shop))

        mapping = self.env['yuju.mapping'].get_mapping(company_id)
        if not mapping:
            return False
        
        id_shop = mapping.id_shop_yuju

        mapping_ids = []
        count_mapping = self.search_count([('product_id', '=', int(product_id)), ('id_shop_yuju', '=', id_shop)])
        if count_mapping > 0:
            mapping_ids = self.search([('product_id', '=', int(product_id)), ('id_shop_yuju', '=', id_shop)], limit=1)
        logger.debug(mapping_ids)
        return mapping_ids

    # def get_product_mapping_by_sku(self, sku):
    #     mapping_ids = self.search([('default_code', '=', sku)])
    #     return mapping_ids

    def get_product_mapping_by_product(self, product_id, only_active=False):
        domain = [('product_id', '=', product_id)]
        if only_active:
            domain.append(('state', '=', 'active'))
        product_mapping = self.search(domain)
        if product_mapping.ids:
            return product_mapping
        return []


class YujuMappingModel(models.Model):
    _name = "yuju.mapping.model"
    _description = 'Yuju Mapping Model'

    name = fields.Char('Modelo Mapeo')
    code = fields.Char('Codigo')

class YujuMappingField(models.Model):
    _name = "yuju.mapping.field"
    _description = 'Yuju Mapping Fields'

    name = fields.Char('Yuju Field')
    field = fields.Char('Odoo Field')
    default_value = fields.Char('Odoo Field Default Value')
    fieldtype = fields.Selection([('integer', 'Numerico'), ('char', 'Cadena'), ('relation', 'Relacional')], 'Odoo Field Type')
    model = fields.Many2one('yuju.mapping.model', 'Modelo Mapeo')
    model_relation = fields.Many2one('yuju.mapping.model', 'Modelo Relacion')
    field_values = fields.One2many('yuju.mapping.field.value', 'field_id', 'Valores campos')
    company_id = fields.Many2one('res.company', 'Company')

    @api.model
    def update_mapping_fields(self, record_data, modelo):
        
        logger.debug(f"## Se buscan mapeo de campos {modelo} ##")
        logger.debug(record_data)
        # field_values = self.env['yuju.mapping.field.value']
        mapping_model = self.env['yuju.mapping.model'].search([('code', '=', modelo)], limit=1)
        
        if not mapping_model: 
            logger.debug(f"No se encontraron mapeos para el modelo {modelo}")
            return record_data

        company_id = self.env.user.company_id.id
        mapping_fields = self.search([('model', '=', mapping_model.id), '|', ('company_id', '=', company_id), ('company_id', '=', False)])

        logger.debug("Mappings encontrados")
        logger.debug(mapping_fields)
        
        for mapping in mapping_fields:
            yuju_field = mapping.name
            odoo_field = mapping.field
            default_value = mapping.default_value 
            tipo = mapping.fieldtype
            model_rel = mapping.model_relation

            mapping_value = None

            logger.debug(yuju_field)

            if yuju_field in record_data:
                yuju_value = record_data.pop(yuju_field)

                if tipo == "relation":
                    try:
                        model_code = model_rel.code
                        rel_value = self.env[model_code].search(['|', ('name', '=', yuju_value), ('code', '=', yuju_value)], limit=1)
                    except Exception as e:
                        logger.error(f'No se pudo obtener informacion del modelo {model_code}, validar que el modelo exista y tenga acceso, {e}')
                    else:
                        logger.debug(f"Valor encontrado en el mapeo {yuju_value}, del modelo {model_code}: {rel_value}")
                        mapping_value = rel_value.id
                else:
                        
                    if not mapping.field_values:
                        if default_value:
                            mapping_value = default_value
                        else:
                            mapping_value = yuju_value
                    else:
                        mapping_value_id = mapping.field_values.search([('name', '=', yuju_value)], limit=1)
                        # mapping_value_id = field_values.search([('field_id', '=', mapping.id), ('name', '=', yuju_value)], limit=1)

                        if mapping_value_id:
                            mapping_value = mapping_value_id.value
                        else:
                            if default_value:
                                mapping_value = default_value
                            else:
                                mapping_value = yuju_value

            if mapping_value:

                if tipo in ['integer']:
                    mapping_value = int(mapping_value)

                update_data = {odoo_field : mapping_value}
                logger.debug(f"#Actualiza datos por campos mapeados {update_data}")

                record_data.update(update_data)

        return record_data

class YujuMappingFieldValue(models.Model):
    _name = "yuju.mapping.field.value"
    _description = 'Yuju Mapping Fields Values'

    name = fields.Char('Yuju Value')
    value = fields.Char('Odoo Value')
    field_id = fields.Many2one('yuju.mapping.field', 'Odoo Field')

class YujuMappingCustom(models.Model):
    _name = "yuju.mapping.custom"
    _description = 'Yuju Mapping Custom Orders'

    name = fields.Char('Campo')
    value = fields.Char('Valor por defecto')
    value_type = fields.Selection([('number', 'Numero'), ('char', 'Cadena')], default='char', string='Tipo de Valor')
    custom_values = fields.One2many('yuju.mapping.custom.value', 'custom_id', 'Valores custom')
    modelo = fields.Selection(
        [('sales', 'Ventas'), ('invoices', 'Facturas')], 'Tipo de modelo')
    company_id = fields.Many2one('res.company', 'Company')

    @api.model
    def get_defect_values(self, modelo='sales'):        
        default_values = {}
        company_id = self.env.user.company_id.id
        mapping_custom = self.search([('modelo', '=', modelo), '|', ('company_id', '=', company_id), ('company_id', '=', False)])
        if mapping_custom.ids:
            logger.debug("## Default 1")
            for el in mapping_custom:
                if el.name:
                    custom_field = el.name
                    custom_default = el.value

                    if el.value_type == 'number':
                        custom_default = int(custom_default)

                    default_values.update({custom_field : custom_default})
        return default_values

    @api.model
    def update_custom_values(self, fulfillment, channel_id, modelo='sales'):        
        custom_data = {}
        company_id = self.env.user.company_id.id
        mapping_custom = self.search([('modelo', '=', modelo), '|', ('company_id', '=', company_id), ('company_id', '=', False)])
        if mapping_custom.ids:
            logger.debug("## Custom 1")
            for el in mapping_custom:
                custom_field = el.name
                custom_default = el.value
                rule_found = False
                for custom_v in el.custom_values:
                    if custom_v.channel_id == str(channel_id) and custom_v.ff_type == str(fulfillment):
                        custom_data.update({custom_field : custom_v.name})
                        rule_found = True
                        break
                if not rule_found:
                    custom_data.update({custom_field : custom_default})
        return custom_data
    
class YujuMappingCustomValue(models.Model):
    _name = "yuju.mapping.custom.value"
    _description = 'Yuju Mapping Custom Values'

    name = fields.Char('Valor Custom')
    channel_id = fields.Char('Channel Id')
    ff_type = fields.Char('FF Type')
    custom_id = fields.Many2one('yuju.mapping.custom', 'Campo custom')
