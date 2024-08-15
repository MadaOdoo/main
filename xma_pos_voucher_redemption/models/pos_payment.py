# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosPayment(models.Model):
    _inherit = 'pos.payment'

    def _export_for_ui(self, payment):
        res = super(PosPayment, self)._export_for_ui(payment)
        print("="*50)
        print(payment)
        res["transaction_id"] = payment.transaction_id
        return res