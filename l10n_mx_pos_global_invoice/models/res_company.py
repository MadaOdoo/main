# -*- coding: utf-8 -*-

from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    apply_global_invoice = fields.Boolean(string="Aplica factura global")