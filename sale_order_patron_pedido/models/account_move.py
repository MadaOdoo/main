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

class AccountMove(models.Model):
    _inherit = "account.move"

    show_tallas_enteras = fields.Boolean(string="Mostrar Tallas enteras",
        compute="compute_campo_show_tallas_enteras")

    move_line_talla_ids = fields.One2many('account.move.line.talla','move_id',string="Cuadro de tallas")
    #######################################################################################################

    has_talla_21_5 = fields.Boolean(string="21.5", compute="compute_campo_has_talla_21_5",store=True)
    has_talla_22_5 = fields.Boolean(string="22.5", compute="compute_campo_has_talla_22_5",store=True)
    has_talla_23_5 = fields.Boolean(string="23.5", compute="compute_campo_has_talla_23_5",store=True)
    has_talla_24_5 = fields.Boolean(string="24.5", compute="compute_campo_has_talla_24_5",store=True)
    has_talla_25_5 = fields.Boolean(string="25.5", compute="compute_campo_has_talla_25_5",store=True)
    has_talla_26_5 = fields.Boolean(string="26.5", compute="compute_campo_has_talla_26_5",store=True)
    has_talla_27_5 = fields.Boolean(string="27.5", compute="compute_campo_has_talla_27_5",store=True)

    #######################################################################################################

    contador_items_totales = fields.Integer(string="Cantidad Items",
        compute="compute_campo_contador_items_totales")

    contador_numero_total_productos = fields.Integer(string="Número Total Productos",
        compute="compute_campo_contador_numero_total_productos")


    @api.depends('invoice_line_ids','invoice_line_ids.product_template_id')
    def compute_campo_contador_items_totales(self):
        for rec in self:
            rec.contador_items_totales = 0
            if rec.invoice_line_ids:
                rec.contador_items_totales = len(rec.invoice_line_ids.mapped('product_template_id') or '')


    @api.depends('invoice_line_ids', 'invoice_line_ids.quantity')
    def compute_campo_contador_numero_total_productos(self):
        for rec in self:
            rec.contador_numero_total_productos = sum(rec.invoice_line_ids.mapped('quantity') or [])

    #########################################################################################################################
    def action_post(self):
        result = super(AccountMove,self).action_post()

        for rec in self:
            rec.calculate_move_line_talla_ids()

        return result

    ######################################################################################################

    def calculate_move_line_talla_ids(self):
        for rec in self:
            rec.move_line_talla_ids.unlink()

            array = []
            array_template = {}

            for line in rec.invoice_line_ids:

                if line.has_uom_par and line.product_id:

                    name_talla = line.product_id.product_template_variant_value_ids and line.product_id.product_template_variant_value_ids[0] \
                        and line.product_id.product_template_variant_value_ids[0].name or ''

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
                                    array_template[line.product_template_id.id][format_name_talla] += (line.quantity or 0.00)
                                else:
                                    array_template[line.product_template_id.id][format_name_talla] = (line.quantity or 0.00)

                                array_template[line.product_template_id.id]['product_uom_qty'] += (line.quantity or 0.00)
                                array_template[line.product_template_id.id]['price_subtotal'] += line.price_subtotal 
                                array_template[line.product_template_id.id]['price_total'] += line.price_total 
                            else:
                                array_template[line.product_template_id.id] = {}
                                array_template[line.product_template_id.id][format_name_talla] = (line.quantity or 0.00)
                                array_template[line.product_template_id.id]['product_uom_qty'] = (line.quantity or 0.00)
                                array_template[line.product_template_id.id]['price_subtotal'] = line.price_subtotal 
                                array_template[line.product_template_id.id]['price_total'] = line.price_total 

                            ###############################################################################################
                            array_template[line.product_template_id.id]['move_id'] = rec.id
                            array_template[line.product_template_id.id]['move_line_id'] = False
                            array_template[line.product_template_id.id]['product_id'] = False
                            array_template[line.product_template_id.id]['product_template_id'] = line.product_template_id.id
                            array_template[line.product_template_id.id]['l10n_mx_edi_customs_number'] = line.l10n_mx_edi_customs_number or ''
                            array_template[line.product_template_id.id]['price_unit'] = line.price_unit or 0.00
                            array_template[line.product_template_id.id]['tax_id'] = line.tax_ids.ids or False
                            array_template[line.product_template_id.id]['unspsc_code_id'] = line.product_id.unspsc_code_id and line.product_id.unspsc_code_id.id or False
                            array_template[line.product_template_id.id]['product_uom'] = line.product_uom_id and line.product_uom_id.id or False
                            array_template[line.product_template_id.id]['discount'] = line.discount or 0.00

                elif line.product_id:
                    array.append({
                        'move_id':rec.id,
                        'move_line_id':line.id,
                        'product_id':line.product_id.id,
                        'unspsc_code_id':line.product_id.unspsc_code_id and line.product_id.unspsc_code_id.id or False,
                        'product_template_id':line.product_template_id.id,
                        'l10n_mx_edi_customs_number':line.l10n_mx_edi_customs_number or '',
                        'product_uom':line.product_uom_id and line.product_uom_id.id or False,
                        'product_uom_qty':line.quantity or 0.00,
                        'price_unit':line.price_unit or 0.00,
                        'tax_id':line.tax_ids.ids or False,
                        'price_subtotal':line.price_subtotal or 0.00,
                        'price_total':line.price_total or 0.00,
                        'discount':line.discount or 0.00,
                    })


            for line2 in array_template:
                rec.move_line_talla_ids.create(array_template[line2])

            rec.move_line_talla_ids.create(array)
        
    ########################################################################################################

    @api.depends('move_line_talla_ids', 'move_line_talla_ids.has_talla_21_5')
    def compute_campo_has_talla_21_5(self):
        for rec in self:

            rec.has_talla_21_5 = False
            if rec.move_line_talla_ids.filtered(lambda t: t.has_talla_21_5):
                rec.has_talla_21_5 = True


    @api.depends('move_line_talla_ids', 'move_line_talla_ids.has_talla_22_5')
    def compute_campo_has_talla_22_5(self):
        for rec in self:

            rec.has_talla_22_5 = False
            if rec.move_line_talla_ids.filtered(lambda t: t.has_talla_22_5):
                rec.has_talla_22_5 = True

    @api.depends('move_line_talla_ids', 'move_line_talla_ids.has_talla_23_5')
    def compute_campo_has_talla_23_5(self):
        for rec in self:

            rec.has_talla_23_5 = False
            if rec.move_line_talla_ids.filtered(lambda t: t.has_talla_23_5):
                rec.has_talla_23_5 = True

    @api.depends('move_line_talla_ids', 'move_line_talla_ids.has_talla_24_5')
    def compute_campo_has_talla_24_5(self):
        for rec in self:

            rec.has_talla_24_5 = False
            if rec.move_line_talla_ids.filtered(lambda t: t.has_talla_24_5):
                rec.has_talla_24_5 = True

    @api.depends('move_line_talla_ids', 'move_line_talla_ids.has_talla_25_5')
    def compute_campo_has_talla_25_5(self):
        for rec in self:

            rec.has_talla_25_5 = False
            if rec.move_line_talla_ids.filtered(lambda t: t.has_talla_25_5):
                rec.has_talla_25_5 = True

    @api.depends('move_line_talla_ids', 'move_line_talla_ids.has_talla_26_5')
    def compute_campo_has_talla_26_5(self):
        for rec in self:

            rec.has_talla_26_5 = False
            if rec.move_line_talla_ids.filtered(lambda t: t.has_talla_26_5):
                rec.has_talla_26_5 = True

    @api.depends('move_line_talla_ids', 'move_line_talla_ids.has_talla_27_5')
    def compute_campo_has_talla_27_5(self):
        for rec in self:

            rec.has_talla_27_5 = False
            if rec.move_line_talla_ids.filtered(lambda t: t.has_talla_27_5):
                rec.has_talla_27_5 = True

    #########################################################################################################
    @api.depends('invoice_line_ids','invoice_line_ids.has_uom_par')
    def compute_campo_show_tallas_enteras(self):
        for rec in self:
            rec.show_tallas_enteras = False

            if rec.invoice_line_ids.filtered(lambda t: t.has_uom_par):
                rec.show_tallas_enteras = True


    ##########################################################################################################

    def _get_order_talla_lines_to_report(self):

        #self.calculate_move_line_talla_ids()
        down_payment_lines = self.move_line_talla_ids.filtered(lambda line:
            (line.move_line_id and 
            line.move_line_id.is_downpayment and not 
            line.move_line_id.display_type and not 
            line.move_line_id._get_downpayment_state()) or not line.move_line_id
        )

        def show_line(line):
            if not line.move_line_id:
                return True
            if line.move_line_id and not line.move_line_id.is_downpayment:
                return True
            elif line.move_line_id and line.move_line_id.display_type and down_payment_lines:
                return True  # Only show the down payment section if down payments were posted
            elif line in down_payment_lines:
                return True  # Only show posted down payments
            else:
                return False

        return self.move_line_talla_ids.filtered(show_line)



class AccountMoveLine(models.Model):
    _inherit = "account.move.line"


    product_template_id = fields.Many2one('product.template',string="Plantilla de Producto",
        compute="compute_campo_product_template_id")

    product_template_image = fields.Binary(
        string="Imagen", related='product_template_id.image_128')

    has_uom_par = fields.Boolean(string="Tiene unidad de medida par", compute="compute_campo_has_uom_par")


    @api.depends('product_id')
    def compute_campo_product_template_id(self):
        for rec in self:
            rec.product_template_id = False
            if rec.product_id:
                rec.product_template_id = rec.product_id.product_tmpl_id or False



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
