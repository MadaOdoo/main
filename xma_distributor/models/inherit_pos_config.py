from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    global_invoice_method = fields.Selection(
        string="Method",
        selection=[
            ('manual', 'Manual')
        ],
        default='manual',
        required=False
    )
    global_customer_id = fields.Many2one(
        comodel_name="res.partner",
        string="Cliente global",
        required=False,
        default=928
    )