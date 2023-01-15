# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, models, fields, api


class AccountMoveInherit(models.Model):
    _inherit = ['account.move']

    source_order_id = fields.Many2one('sale.order', string='Orden de Venta relacionada')
