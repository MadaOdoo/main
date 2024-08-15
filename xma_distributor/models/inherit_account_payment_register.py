# -*- coding: utf-8 -*-

from odoo import models, fields

class InheritAccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    pos_order_ids = fields.Many2many(
        "pos.order",
        string="Ordenes POS"
    )