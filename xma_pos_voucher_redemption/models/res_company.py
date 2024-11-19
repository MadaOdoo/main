# -*- coding: utf-8 -*-

from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    apply_voucher = fields.Boolean(string="Aplica vales")