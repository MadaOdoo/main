# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, timedelta, datetime
from odoo.exceptions import UserError, ValidationError

class InheritPosOrder(models.Model):
    _inherit = 'pos.payment'

    distribuidora_id = fields.Many2one(
        "res.partner",
        string="Distribuidora",
        related="pos_order_id.distribuidora_id",
        store=True
    )
    apply_voucher = fields.Boolean(related="company_id.apply_voucher")