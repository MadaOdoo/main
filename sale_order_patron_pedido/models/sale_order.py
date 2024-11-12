# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

UOM_PAR = 'par'

ARRAY_CAMPOS_TALLAS = [
    'talla_21',
    'talla_21_5',
    'talla_22',
    'talla_22_5',
    'talla_23',
    'talla_23_5',
    'talla_24',
    'talla_24_5',
    'talla_25',
    'talla_25_5',
    'talla_26',
    'talla_26_5',
    'talla_27',
    'talla_27_5',
    'talla_28'
    ]

class SaleOrder(models.Model):
    _inherit = "sale.order"

    show_tallas_enteras = fields.Boolean(string="Mostrar Tallas enteras",
        compute="compute_campo_show_tallas_enteras")

    order_line_talla_ids = fields.One2many('sale.order.line.talla','order_id',string="Cuadro de tallas")
    #######################################################################################################

    has_talla_21_5 = fields.Boolean(string="21.5", compute="compute_campo_has_talla_21_5",store=True)
    has_talla_22_5 = fields.Boolean(string="22.5", compute="compute_campo_has_talla_22_5",store=True)
    has_talla_23_5 = fields.Boolean(string="23.5", compute="compute_campo_has_talla_23_5",store=True)
    has_talla_24_5 = fields.Boolean(string="24.5", compute="compute_campo_has_talla_24_5",store=True)
    has_talla_25_5 = fields.Boolean(string="25.5", compute="compute_campo_has_talla_25_5",store=True)
    has_talla_26_5 = fields.Boolean(string="26.5", compute="compute_campo_has_talla_26_5",store=True)
    has_talla_27_5 = fields.Boolean(string="27.5", compute="compute_campo_has_talla_27_5",store=True)
    ########################################################################################################

    contador_items_totales = fields.Integer(string="Cantidad Items",
                                            compute="compute_campo_contador_items_totales")

    contador_numero_total_productos = fields.Integer(string="Número Total Productos",
                                            compute="compute_campo_contador_numero_total_productos")


    @api.depends('order_line','order_line.product_template_id')
    def compute_campo_contador_items_totales(self):
        for rec in self:
            rec.contador_items_totales = 0
            if rec.order_line:
                rec.contador_items_totales = len(rec.order_line.mapped('product_template_id') or '')


    @api.depends('order_line', 'order_line.product_uom_qty')
    def compute_campo_contador_numero_total_productos(self):
        for rec in self:
            rec.contador_numero_total_productos = sum(rec.order_line.mapped('product_uom_qty') or [])

    #########################################################################################################################

    def calculate_order_line_talla_ids(self):
        for rec in self:
            rec.order_line_talla_ids.unlink()

            array = []
            array_template = {}

            for line in rec.order_line:

                if line.has_uom_par and line.product_id:

                    name_talla = line.product_id.product_template_variant_value_ids and line.product_id.product_template_variant_value_ids[0] and line.product_id.product_template_variant_value_ids[0].name or ''

                    format_name_talla = ''
                    
                    if name_talla:

                        partes = name_talla.split('.')
                        if len(partes or '')>1:
                            format_name_talla = "talla_%s_%s"%(partes[0] or '',partes[1] or '')
                        else:
                            format_name_talla = "talla_%s"%(partes[0] or '')
                        
                        if format_name_talla in ARRAY_CAMPOS_TALLAS:

                            if line.product_template_id.id in array_template:
                            
                                if format_name_talla in array_template[line.product_template_id.id]:
                                    array_template[line.product_template_id.id][format_name_talla] += (line.product_uom_qty or 0.00)
                                else:
                                    array_template[line.product_template_id.id][format_name_talla] = (line.product_uom_qty or 0.00)

                                array_template[line.product_template_id.id]['product_uom_qty'] += (line.product_uom_qty or 0.00)
                                array_template[line.product_template_id.id]['price_subtotal'] += line.price_subtotal 
                                array_template[line.product_template_id.id]['price_total'] += line.price_total 
                            else:
                                array_template[line.product_template_id.id] = {}
                                array_template[line.product_template_id.id][format_name_talla] = (line.product_uom_qty or 0.00)
                                array_template[line.product_template_id.id]['product_uom_qty'] = (line.product_uom_qty or 0.00)
                                array_template[line.product_template_id.id]['price_subtotal'] = line.price_subtotal
                                array_template[line.product_template_id.id]['price_total'] = line.price_total 

                            ###############################################################################################
                            array_template[line.product_template_id.id]['order_id'] = rec.id
                            array_template[line.product_template_id.id]['order_line_id'] = False
                            array_template[line.product_template_id.id]['product_id'] = False
                            array_template[line.product_template_id.id]['product_template_id'] = line.product_template_id.id
                            array_template[line.product_template_id.id]['price_unit'] = line.price_unit or 0.00
                            array_template[line.product_template_id.id]['tax_id'] = line.tax_id.ids or False
                            array_template[line.product_template_id.id]['product_uom'] = line.product_uom and line.product_uom.id or False
                            array_template[line.product_template_id.id]['discount'] = line.discount or 0.00

                elif line.product_id:
                    array.append({
                        'order_id':rec.id,
                        'order_line_id':line.id,
                        'product_id':line.product_id.id,
                        'product_template_id':line.product_template_id.id,
                        'product_uom':line.product_uom and line.product_uom.id or False,
                        'product_uom_qty':line.product_uom_qty or 0.00,
                        'price_unit':line.price_unit or 0.00,
                        'tax_id':line.tax_id.ids or False,
                        'price_subtotal':line.price_subtotal or 0.00,
                        'price_total':line.price_total or 0.00,
                        'discount':line.discount or 0.00,
                    })

            ### Creando las lineas secundarias
            _logger.info('\n\nARRAY TEMPLATE\n\n')
            _logger.info(array_template)

            for line2 in array_template:
                _logger.info('\n\nITEM DE ARRAY TEMPLATE\n\n')
                _logger.info(array_template[line2])
                rec.order_line_talla_ids.create(array_template[line2])

            rec.order_line_talla_ids.create(array)
        
    ########################################################################################################

    @api.depends('order_line_talla_ids', 'order_line_talla_ids.has_talla_21_5')
    def compute_campo_has_talla_21_5(self):
        for rec in self:

            rec.has_talla_21_5 = False
            if rec.order_line_talla_ids.filtered(lambda t: t.has_talla_21_5):
                rec.has_talla_21_5 = True


    @api.depends('order_line_talla_ids', 'order_line_talla_ids.has_talla_22_5')
    def compute_campo_has_talla_22_5(self):
        for rec in self:

            rec.has_talla_22_5 = False
            if rec.order_line_talla_ids.filtered(lambda t: t.has_talla_22_5):
                rec.has_talla_22_5 = True

    @api.depends('order_line_talla_ids', 'order_line_talla_ids.has_talla_23_5')
    def compute_campo_has_talla_23_5(self):
        for rec in self:

            rec.has_talla_23_5 = False
            if rec.order_line_talla_ids.filtered(lambda t: t.has_talla_23_5):
                rec.has_talla_23_5 = True

    @api.depends('order_line_talla_ids', 'order_line_talla_ids.has_talla_24_5')
    def compute_campo_has_talla_24_5(self):
        for rec in self:

            rec.has_talla_24_5 = False
            if rec.order_line_talla_ids.filtered(lambda t: t.has_talla_24_5):
                rec.has_talla_24_5 = True

    @api.depends('order_line_talla_ids', 'order_line_talla_ids.has_talla_25_5')
    def compute_campo_has_talla_25_5(self):
        for rec in self:

            rec.has_talla_25_5 = False
            if rec.order_line_talla_ids.filtered(lambda t: t.has_talla_25_5):
                rec.has_talla_25_5 = True

    @api.depends('order_line_talla_ids', 'order_line_talla_ids.has_talla_26_5')
    def compute_campo_has_talla_26_5(self):
        for rec in self:

            rec.has_talla_26_5 = False
            if rec.order_line_talla_ids.filtered(lambda t: t.has_talla_26_5):
                rec.has_talla_26_5 = True

    @api.depends('order_line_talla_ids', 'order_line_talla_ids.has_talla_27_5')
    def compute_campo_has_talla_27_5(self):
        for rec in self:

            rec.has_talla_27_5 = False
            if rec.order_line_talla_ids.filtered(lambda t: t.has_talla_27_5):
                rec.has_talla_27_5 = True

    #########################################################################################################
    @api.depends('order_line','order_line.has_uom_par')
    def compute_campo_show_tallas_enteras(self):
        for rec in self:
            rec.show_tallas_enteras = False

            if rec.order_line.filtered(lambda t: t.has_uom_par):
                rec.show_tallas_enteras = True

    ##########################################################################################################

    def _get_matrix(self, product_template):
        res = super(SaleOrder, self)._get_matrix(product_template)

        record_patron = []

        patron_ids = self.partner_id.patron_pedido_line_ids

        if product_template.uom_id.name.lower() == UOM_PAR:
            
            tallas = ['talla_21', 'talla_21_5', 'talla_22', 'talla_22_5', 'talla_23', 'talla_23_5', 'talla_24',
                      'talla_24_5', 'talla_25', 'talla_25_5', 'talla_26', 'talla_26_5', 'talla_27', 'talla_27_5',
                      'talla_28']
            talla_ref = {}

            attribute_lines = product_template.valid_product_template_attribute_line_ids
            attribute_ids_by_line = [line.product_template_value_ids._only_active() for line in attribute_lines]

            for line in attribute_ids_by_line:
                for ptv in line:
                    t_val = 'talla_%s' % ptv.name.replace('.', '_')
                    if t_val in tallas:
                        talla_ref[t_val] = ptv.id

            for p in patron_ids:
                val = {
                    'id': p.id,
                    'name': p.name_corrida,
                    'tallas': {t: p[k] for k, t in talla_ref.items()},
                }
                record_patron.append(val)
            res['record_patron'] = record_patron
            res['has_record_patron'] = True if patron_ids else False

        return res
    
    ##########################################################################################################

    def _get_order_talla_lines_to_report(self):

        #self.calculate_order_line_talla_ids()
        down_payment_lines = self.order_line_talla_ids.filtered(lambda line:
            (line.order_line_id and 
            line.order_line_id.is_downpayment and not 
            line.order_line_id.display_type and not 
            line.order_line_id._get_downpayment_state()) or not line.order_line_id
        )

        def show_line(line):
            if not line.order_line_id:
                return True
            if line.order_line_id and not line.order_line_id.is_downpayment:
                return True
            elif line.order_line_id and line.order_line_id.display_type and down_payment_lines:
                return True  # Only show the down payment section if down payments were posted
            elif line in down_payment_lines:
                return True  # Only show posted down payments
            else:
                return False

        return self.order_line_talla_ids.filtered(show_line)



class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"


    product_template_image = fields.Binary(
        string="Imagen", 
        related='product_template_id.image_128')

    has_uom_par = fields.Boolean(string="Tiene unidad de medida par", compute="compute_campo_has_uom_par")

    @api.depends('product_template_id')
    def compute_campo_has_uom_par(self):
        for rec in self:

            rec.has_uom_par = False

            if rec.product_template_id and rec.product_template_id.uom_id:
                name_uom = rec.product_template_id.uom_id.name or ''

                if name_uom.lower() == UOM_PAR:
                    rec.has_uom_par = True
                else:
                    rec.has_uom_par = False