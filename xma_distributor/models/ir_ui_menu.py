# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
from collections import defaultdict
import operator
import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.modules import get_module_resource
from odoo.osv import expression

MENU_ITEM_SEPARATOR = "/"
NUMBER_PARENS = re.compile(r"\(([0-9]+)\)")


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    @tools.ormcache('frozenset(self.env.user.groups_id.ids)', 'debug')
    def _visible_menu_ids(self, debug=False):
        res = super(IrUiMenu, self)._visible_menu_ids(debug)
        if (
            not self.env.company.apply_voucher
            and self.env.ref(
                "xma_distributor.voucher_reports_management_menu"
            ).id in res
        ):
            res.remove(self.env.ref(
                "xma_distributor.voucher_reports_management_menu"
            ).id)
        return res