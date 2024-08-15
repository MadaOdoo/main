# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InheritResPartner(models.Model):
    _inherit = 'res.partner'

    curp = fields.Char(
        string='Curp',
    )

    @api.model
    def validar_curp(self, curp, partner_id):
        count_partners = 0
        if partner_id:
            count_partners = self.search_count(
                [
                    ('curp','=',curp),
                    ('id','!=',partner_id),
                ],
                limit=1
            )
        else:
            count_partners = self.search_count(
                [
                    ('curp','=',curp),
                ],
                limit=1
            )
        if count_partners:
            return True
        else:
            return False
