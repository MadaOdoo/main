# -*- coding: utf-8 -*-

from odoo import models, fields

class InheritAccountJournal(models.Model):
    _inherit = 'account.journal'

    is_vale = fields.Boolean(string='Es de vales')
    partner = fields.Many2one(
        'res.partner',
        string='Cliente',
    )
    apply_voucher = fields.Boolean(related="company_id.apply_voucher")

