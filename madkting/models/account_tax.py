# -*- coding: utf-8 -*-
# File:           res_partner.py
# Author:         Israel Calderón
# Copyright:      (C) 2019 All rights reserved by Madkting
# Created:        2019-07-15
from odoo import models, api


class AccountTax(models.Model):
    _inherit = 'account.tax'

    @api.model
    def get_sale_taxes_ids(self, company_id, amounts):
        """
        Retrieves sale taxes ids into a list (only ids not models)
        :param company_id: company_id where the taxes must belong
        :type company_id: int
        :param amounts: amounts for taxes
        :type amounts: list
        :return: list of taxes ids
        :rtype: list
        """
        return self.env['account.tax'] \
                   .search([('type_tax_use', '=', 'sale'),
                            ('amount', '=', amounts),
                            ('active', '=', True),
                            ('company_id', '=', company_id)]) \
                   .ids
