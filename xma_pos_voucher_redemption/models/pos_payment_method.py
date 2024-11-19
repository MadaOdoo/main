# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    is_bank_terminal = fields.Boolean(string="Es terminal bancaria?")
    apply_voucher = fields.Boolean(related="company_id.apply_voucher")