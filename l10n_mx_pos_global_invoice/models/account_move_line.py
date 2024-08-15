from odoo import fields, models
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    
    check_global_invoice = fields.Boolean(
        string='check global invoice',
    )

