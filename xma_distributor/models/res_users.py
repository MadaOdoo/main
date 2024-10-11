from odoo import fields, models
from odoo.exceptions import UserError


class ResUsers(models.Model):
    _inherit = "res.users"

    password_api = fields.Char(
        readonly=False,
        string="Key API"
    )

    apply_voucher = fields.Boolean(related="company_id.apply_voucher")