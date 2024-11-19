from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    global_customer_id = fields.Many2one(
        comodel_name="res.partner",
        string="Cliente global",
        required=False,
    )
    create_global_invoice = fields.Boolean(
        string="Crear factura global",
    )
    global_invoice_method = fields.Selection(
        string="Method",
        selection=[
            ('manual', 'Manual'),
            #('automatic', 'Automatico'),
        ],
    )
    global_journal_id = fields.Many2one(
        'account.journal', string='Diario',)

    global_periodicity = fields.Selection(
        string="Periodicidad",
        selection=[
            ('01', 'Diario'),
            ('02', 'Semanal'),
            ('03', 'Quincenal'),
            ('04', 'Mensual'),
            ('05', 'Bimestral'),
        ]
    )
    apply_global_invoice = fields.Boolean(related="company_id.apply_global_invoice")
