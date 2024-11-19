# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InheritResPartner(models.Model):
    _inherit = 'res.partner'

    curp = fields.Char(
        string='INE',
    )
    apply_voucher = fields.Boolean(related="company_id.apply_voucher")

    @api.model
    def validar_curp(self, l10n_mx_edi_curp, partner_id):
        count_partners = 0
        if partner_id:
            count_partners = self.search_count(
                [
                    ('l10n_mx_edi_curp','=',l10n_mx_edi_curp),
                    ('id','!=',partner_id),
                ],
                limit=1
            )
        else:
            count_partners = self.search_count(
                [
                    ('l10n_mx_edi_curp','=',l10n_mx_edi_curp),
                ],
                limit=1
            )
        if count_partners:
            return True
        else:
            return False

    @api.model
    def create_from_ui(self, partner):
        company_id = False
        if 'id' in partner and partner['id'] == False:
            company_id = self.env.company.id
        partner_id = super().create_from_ui(partner)
        if company_id:
            self.browse(partner_id).write({
                'company_id': company_id
            })
        return partner_id
