from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    global_invoice_method = fields.Selection(
        string="Method",
        selection=[
            ('manual', 'Manual')
        ],
        default='manual',
        #readonly=True,
        required=False
    )