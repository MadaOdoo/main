# -*- coding: utf-8 -*-

from odoo import models, fields

class InheritAccountMoveLinet(models.Model):
    _inherit = 'account.move.line'

    distribuidora_id = fields.Many2one(
        'res.partner',
        string='Distribuidora',
    )