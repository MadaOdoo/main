# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import logging
from itertools import *
from datetime import datetime, timedelta

class AccountMoveLineTalla(models.Model):
    _name = 'account.move.line.talla'
    _description = "Tabla de tallas en factura"

    move_id = fields.Many2one('account.move',string="Factura",ondelete="cascade")
    move_line_id = fields.Many2one('account.move.line',string="Linea de Factura")

    product_template_id = fields.Many2one('product.template',string="Producto")

    product_template_image = fields.Binary(
        string="Imagen", 
        related='product_template_id.image_128')

    product_id = fields.Many2one('product.product',string="Variante")

    unspsc_code_id = fields.Many2one('product.unspsc.code',string="Código Producto")


    product_uom_qty = fields.Float(string="Cantidad")
    product_uom = fields.Many2one('uom.uom',string="UdM")
    price_unit = fields.Float(string="Precio Unitario")
    tax_id = fields.Many2many('account.tax',string="Impuestos")
    price_subtotal = fields.Float(string="Subtotal")
    price_total = fields.Float(string="Total")
    discount = fields.Float(string="Desc.%")

    talla_21 = fields.Integer(string="21")
    talla_21_5 = fields.Integer(string="21.5")
    talla_22 = fields.Integer(string="22")
    talla_22_5 = fields.Integer(string="22.5")
    talla_23 = fields.Integer(string="23")
    talla_23_5 = fields.Integer(string="23.5")
    talla_24 = fields.Integer(string="24")
    talla_24_5 = fields.Integer(string="24.5")
    talla_25 = fields.Integer(string="25")
    talla_25_5 = fields.Integer(string="25.5")
    talla_26 = fields.Integer(string="26")
    talla_26_5 = fields.Integer(string="26.5")
    talla_27 = fields.Integer(string="27")
    talla_27_5 = fields.Integer(string="27.5")
    talla_28 = fields.Integer(string="28")

    display_type = fields.Char(string="Tipo de Pantalla",compute="compute_campo_display_type",store=True)

    #############################################################

    has_talla_21_5 = fields.Boolean(string="21.5", compute="compute_campo_has_talla_21_5",store=True)
    has_talla_22_5 = fields.Boolean(string="22.5", compute="compute_campo_has_talla_22_5",store=True)
    has_talla_23_5 = fields.Boolean(string="23.5", compute="compute_campo_has_talla_23_5",store=True)
    has_talla_24_5 = fields.Boolean(string="24.5", compute="compute_campo_has_talla_24_5",store=True)
    has_talla_25_5 = fields.Boolean(string="25.5", compute="compute_campo_has_talla_25_5",store=True)
    has_talla_26_5 = fields.Boolean(string="26.5", compute="compute_campo_has_talla_26_5",store=True)
    has_talla_27_5 = fields.Boolean(string="27.5", compute="compute_campo_has_talla_27_5",store=True)

    #############################################################
    has_uom_par = fields.Boolean(string="Tiene unidad de medida par", compute="compute_campo_has_uom_par")

    @api.depends('product_template_id')
    def compute_campo_has_uom_par(self):
        for rec in self:

            rec.has_uom_par = False

            if rec.product_template_id and rec.product_template_id.uom_id:
                factor_inv = rec.product_template_id.uom_id.factor_inv
                if factor_inv == 2.0:
                    rec.has_uom_par = True
                else:
                    rec.has_uom_par = False

    """@api.depends('move_line_id')
    def compute_campo_product_id(self):
        for rec in self:
            rec.product_template_id = False
            rec.product_id = False
            if rec.move_line_id:
                rec.product_template_id = rec.move_line_id.product_template_id or False 
                rec.product_id = rec.move_line_id.product_id or False """


    @api.depends('move_line_id')
    def compute_campo_display_type(self):
        for rec in self:
            rec.display_type = ''
            if rec.move_line_id:
                rec.display_type = rec.move_line_id.display_type or ''

    #########################################################################

    @api.depends('talla_21_5')
    def compute_campo_has_talla_21_5(self):
        for rec in self:

            rec.has_talla_21_5 = False
            if rec.talla_21_5:
                rec.has_talla_21_5 = True


    @api.depends('talla_22_5')
    def compute_campo_has_talla_22_5(self):
        for rec in self:
            rec.has_talla_22_5 = False
            if rec.talla_22_5:
                rec.has_talla_22_5 = True


    @api.depends('talla_23_5')
    def compute_campo_has_talla_23_5(self):
        for rec in self:
            rec.has_talla_23_5 = False
            if rec.talla_23_5:
                rec.has_talla_23_5 = True


    @api.depends('talla_24_5')
    def compute_campo_has_talla_24_5(self):
        for rec in self:
            rec.has_talla_24_5 = False
            if rec.talla_24_5:
                rec.has_talla_24_5 = True


    @api.depends('talla_25_5')
    def compute_campo_has_talla_25_5(self):
        for rec in self:
            rec.has_talla_25_5 = False
            if rec.talla_25_5:
                rec.has_talla_25_5 = True


    @api.depends('talla_26_5')
    def compute_campo_has_talla_26_5(self):
        for rec in self:
            rec.has_talla_26_5 = False
            if rec.talla_26_5:
                rec.has_talla_26_5 = True


    @api.depends('talla_27_5')
    def compute_campo_has_talla_27_5(self):
        for rec in self:
            rec.has_talla_27_5 = False
            if rec.talla_27_5:
                rec.has_talla_27_5 = True

    #########################################################################