# -*- coding: utf-8 -*-

from odoo import models, fields

class InheritAccountPayment(models.Model):
    _inherit = 'account.payment'

    pos_order_ids = fields.Many2many(
        "pos.order",
        string="Ordenes POS"
    )

    folio_vale = fields.Char(string="Folio del vale")

    distribuidora_id = fields.Many2one(
        "res.partner",
        string="Distribuidora"
    )
    
    payment_number_per_folio = fields.Char(string="N° de pago por folio")
    
    voucher_payment_date = fields.Date(string="Fecha de pago prestavale")
