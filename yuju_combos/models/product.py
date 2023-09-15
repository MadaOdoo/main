# -*- coding: utf-8 -*-
# File:           product.py
# Author:         Gerardo Lopez
# Copyright:      (C) 2021 All rights reserved by Yuju
# Created:        2021-12-19

from odoo import models, api, fields
from odoo import exceptions
from collections import defaultdict
from ..log.logger import logger
from ..responses import results
import psycopg2
import copy

class ProductProduct(models.Model):
    _inherit = "product.product"

    yuju_kit = fields.Many2one('mrp.bom', 'Lista de Material Yuju')

    def add_combo(self, product, materials):
        
        new_bom = self.env['mrp.bom'].create({
                    'product_id' : product.id, 
                    'product_tmpl_id' : product.product_tmpl_id.id,
                    'product_qty' : 1,
                    'type' : 'phantom',
                    'bom_line_ids' : materials
                })        
       
        return new_bom

    def _is_combo(self, product_data):
        if product_data.get('is_combo'):
            return True
        return False

    def get_combo_materials(self, materials):        
        kit_components = []
        config = self.env['madkting.config'].get_config()
        for el in materials:
            product_kit_id = el.get('id_product')
            product_kit_qty = el.get('quantity')
            product_kit_sku = el.get('sku')

            if not product_kit_id:
                return results.error_result(code='id_component_empty',
                                        description='El id del componente no se ha definido')

            product_kit = self.search([('id_product_madkting', '=', product_kit_id)], limit=1)
            if not product_kit.id:
                if config.search_kit_by_sku:
                    product_kit = self.search([('default_code', '=', product_kit_sku)], limit=1)
                    if not product_kit.id:
                        return results.error_result(code='component_not_mapped',
                                        description='Alguno de los componentes por SKU no se ha mapeado')
                else:
                    return results.error_result(code='component_not_mapped',
                                        description='Alguno de los componentes no se ha mapeado')

            kit_components.append((0, 0, {
                'product_id' : product_kit.id,
                'product_qty' : product_kit_qty
                }))

        return results.success_result(data=kit_components)

    @api.model
    def update_product(self, product_data, product_type, id_shop=None):        
        
        config = self.env['madkting.config'].get_config()
        product_type_for_kits = config.product_type_for_kits
        my_product_data = copy.deepcopy(product_data)
        product_id = int(my_product_data.get('id', 0))
        product = self.browse(product_id)
        is_combo = False

        if product_type != 'variation' and 'type' in product_data:
            product_data.pop('type')

        if self._is_combo(product_data):
            is_combo = True
            product_data.pop('is_combo')
            product_data.pop('combo_components')
            materials = my_product_data.get('combo_components')
            res_materials = self.get_combo_materials(materials)
            if not res_materials['success']:
                return res_materials
            else:
                kit_components = res_materials['data']
                if config.update_product_type_kits:
                    product_data.update({"type" : product_type_for_kits, "detailed_type" : product_type_for_kits})
                else:
                    if "type" in product_data:
                        product_data.pop("type")
                    if "detailed_type" in product_data:
                        product_data.pop("detailed_type")

        res = super(ProductProduct, self).update_product(product_data, product_type, id_shop)

        if res['success']:
            product = self.browse(product_id)
            route_id = config.mrp_route.id
            if is_combo:
                logger.debug("## Es combo")
                if product.yuju_kit and config.delete_old_bom:
                    logger.debug("## Tiene Ldm")
                    try:
                        logger.debug("## Elimina Ldm anterior")
                        product.yuju_kit.unlink()
                    except Exception as e:
                        logger.error(e)
                        return results.error_result(code='bom_delete',
                                                        description='Ocurrio un error al eliminar la ldm')                                        
                try:
                    logger.debug("## Crear nueva Ldm")
                    new_bom = self.add_combo(product, kit_components)
                except Exception as e:
                    logger.error(e)
                    return results.error_result(code='bom_create',
                                                    description='Ocurrio un error al crear la ldm')
                else:  
                    logger.debug("## Actualiza tipo y Ldm en producto")              
                    product.write({'yuju_kit' : new_bom.id, 'route_ids' : [(4, route_id)]})
            else:
                logger.debug("## No es combo")
                if product.yuju_kit and config.delete_old_bom:
                    logger.debug("## Tiene Ldm")
                    try:
                        logger.debug("## Elimina Ldm anterior")
                        product.yuju_kit.unlink()
                    except Exception as e:
                        logger.error(e)
                        return results.error_result(code='bom_delete',
                                                        description='Ocurrio un error al eliminar la ldm')
                    
                logger.debug("## Actualiza tipo y Ldm en producto")
                product.write({'type': 'product', 'route_ids' : [(3, route_id)]})

        return res

    @api.model
    def create_variation(self, variation_data, id_shop=None):
        logger.debug("### CREATE VAR ###")
        logger.debug(variation_data)
        
        config = self.env['madkting.config'].get_config()
        product_type_for_kits = config.product_type_for_kits
        my_product_data = copy.deepcopy(variation_data)
        variations = [my_product_data]        
        is_combo = True if my_product_data.get('is_combo') else False
       
        if is_combo:
            variation_data.pop('is_combo')
            variation_data.pop('combo_components')
            # Se actualiza el tipo del producto antes de asignar la lista de materiales ya que si no, 
            # se calcula el stock en base a los materiales existentes, lo cual no permite cambiar el tipo
            # si el stock es > 0 
            if config.update_product_type_kits:
                variation_data.update({"type" : product_type_for_kits, "detailed_type" : product_type_for_kits})
            else:
                if "type" in variation_data:
                    variation_data.pop("type")
                if "detailed_type" in variation_data:
                    variation_data.pop("detailed_type")            

        res = super(ProductProduct, self).create_variation(variation_data, id_shop)

        logger.debug("## Response")
        logger.debug(res)

        if res['success'] and is_combo:
            res_data = res['data']
            # res_id = res_data.get('id')
            res_template_id = res_data.get('product_id')
            template = self.browse(int(res_template_id))
            route_id = config.mrp_route.id

            for product_variant in template.product_variant_ids:
                data = product_variant.get_data()

                variation_data = None
                
                # A continuacion se hace un match entre las variaciones recibidas y las variantes del producto creado en odoo, 
                # que correspondan a los atributos asignados.
                for v in range(len(variations)):
                    if all(attrib in variations[v] and variations[v][attrib] == value for attrib, value in data.get('attributes').items() ):
                        variation_data = variations.pop(v)
                        break

                if variation_data:
                    logger.debug("## Variation data ##")
                    logger.debug(variation_data)
                    materials = variation_data.get('combo_components')                        
                    res_materials = self.get_combo_materials(materials)
                    logger.debug(res_materials)                        
                    if not res_materials['success']:
                        return res_materials
                    else:
                        kit_components = res_materials['data']                        
                        try:
                            new_bom = self.add_combo(product_variant, kit_components)
                        except Exception as e:
                            logger.error(e)
                            return results.error_result(code='bom_create_variation',
                                                            description='Ocurrio un error al crear la ldm')
                        else:     
                            try:           
                                product_variant.write({'yuju_kit' : new_bom.id, 'route_ids' : [(4, route_id)]})
                            except Exception as e:
                                logger.error(e)
                                return results.error_result(code='bom_assign_variation',
                                                            description='Ocurrio un error al asignar la ldm') 
        return res

class ProductTemplate(models.Model):

    _inherit = 'product.template'

    @api.model
    def mdk_create(self, product_data, id_shop=None):

        logger.debug("### MDK CREATE COMBO ###")
        logger.debug(product_data)

        products = self.env['product.product']
        config = self.env['madkting.config'].get_config()
        product_type_for_kits = config.product_type_for_kits
        is_combo = False
        
        my_product_data = copy.deepcopy(product_data)
        variations = my_product_data.get('variations', [])
        variation_attributes = my_product_data.get('variation_attributes', None)
        has_variations = True if variation_attributes else False

        if not has_variations:
            if products._is_combo(product_data):
                is_combo = True
                product_data.pop('is_combo')
                materials = product_data.pop('combo_components')
                res_materials = products.get_combo_materials(materials)
                if not res_materials['success']:
                    return res_materials
                else:
                    kit_components = res_materials['data']
                    if config.update_product_type_kits:
                        product_data.update({"type" : product_type_for_kits, "detailed_type" : product_type_for_kits})
                    else:
                        if "type" in product_data:
                            product_data.pop("type")
                        if "detailed_type" in product_data:
                            product_data.pop("detailed_type") 
                    
        else:
            variation_list = []            
            for var in product_data.pop('variations'):
                if products._is_combo(var):
                    is_combo = True
                    var.pop('is_combo')
                    var.pop('combo_components')
                variation_list.append(var)
            product_data.update({'variations' : variation_list})            
    
        res = super(ProductTemplate, self).mdk_create(product_data, id_shop)

        if res['success'] and is_combo:
            res_data = res['data']
            logger.debug(res_data)
            res_id = res_data.get('id')
            res_template_id = res_data.get('template_id')
            route_id = config.mrp_route.id

            if not has_variations:
                logger.debug("## No tiene variaciones ##")
                res_product = products.search([('id', '=', res_id)], limit=1)
                try:
                    new_bom = products.add_combo(res_product, kit_components)
                except Exception as e:
                    logger.error(e)
                    return results.error_result(code='bom_create',
                                                    description='Ocurrio un error al crear la ldm')
                else:     
                    try:           
                        res_product.write({'yuju_kit' : new_bom.id, 'route_ids' : [(4, route_id)]})
                    except Exception as e:
                        logger.error(e)
                        return results.error_result(code='bom_assign',
                                                    description='Ocurrio un error al asignar la ldm')

            else:
                logger.debug("## Si tiene variaciones ##")
                template = self.browse(int(res_template_id))
                logger.debug(template)
                logger.debug(template.product_variant_ids)
                logger.debug(variations)
                for product_variant in template.product_variant_ids:
                    data = product_variant.get_data()

                    variation_data = None
                    
                    # A continuacion se hace un match entre las variaciones recibidas y las variantes del producto creado en odoo, 
                    # que correspondan a los atributos asignados.
                    for v in range(len(variations)):
                        if all(attrib in variations[v] and variations[v][attrib] == value for attrib, value in data.get('attributes').items() ):
                            variation_data = variations.pop(v)
                            break

                    if variation_data:
                        logger.debug("## Variation data ##")
                        logger.debug(variation_data)
                        materials = variation_data.get('combo_components')                        
                        res_materials = products.get_combo_materials(materials)
                        logger.debug(res_materials)                        
                        if not res_materials['success']:
                            return res_materials
                        else:
                            kit_components = res_materials['data']
                            # Se actualiza el tipo del producto antes de asignar la lista de materiales ya que si no, 
                            # se calcula el stock en base a los materiales existentes, lo cual no permite cambiar el tipo
                            # si el stock es > 0 
                            variation_data = {"type" : product_type_for_kits, "detailed_type" : product_type_for_kits}
                            product_variant.write(variation_data)
                            try:
                                new_bom = products.add_combo(product_variant, kit_components)
                            except Exception as e:
                                logger.error(e)
                                return results.error_result(code='bom_create_variation',
                                                                description='Ocurrio un error al crear la ldm')
                            else:     
                                try:           
                                    product_variant.write({'yuju_kit' : new_bom.id, 'route_ids' : [(4, route_id)]})
                                except Exception as e:
                                    logger.error(e)
                                    return results.error_result(code='bom_assign_variation',
                                                                description='Ocurrio un error al asignar la ldm')            
        return res

    @api.model
    def delete_product(self, template_id, id_shop=None):
        bom_res = self.env['mrp.bom'].search([('product_tmpl_id', '=', template_id)])
        if bom_res.ids:
            try:
                bom_res.unlink()
            except Exception as e:
                logger.error(e)
                return results.error_result(code='bom_delete',
                                                    description='Ocurrio un error al eliminar las ldm')

        res = super(ProductTemplate, self).delete_product(template_id, id_shop) 
        return res