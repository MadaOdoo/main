# -*- coding: utf-8 -*-

from odoo import models, fields

class ResConfigSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    apply_global_invoice = fields.Boolean(
        string="Aplica factura global",
        related='company_id.apply_global_invoice',
        store=True,
        readonly=False
    )
