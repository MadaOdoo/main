# -*- coding: utf-8 -*-

from odoo import models, fields

class InheritAccountPayment(models.Model):
    _inherit = 'account.payment'

    control_vales_id = fields.Many2one(
        'control.vales',
        string="rel",
    )
    folio_vale = fields.Char(
        string="Folio del vale",
        readonly=True,
    )
    state_pago_vale = fields.Selection(
        selection=[
            ('por_pagar', 'Por pagar'),
            ('pagado', 'Pagado'),
        ],
        string='Estado del pago del vale',
    )
    state_vale = fields.Char(
        string='Estado de vale',
        readonly=True,
    )
    pos_vale_order_id = fields.Many2one(
        'pos.order',
        string="Orden de vale de PdV",
    )
