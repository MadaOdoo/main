from odoo import models, fields, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_global_invoice = fields.Boolean("Es factura global", default=False)
    periodicidad = fields.Char("Periodicidad")
    apply_global_invoice = fields.Boolean(related="company_id.apply_global_invoice")

    def unlink(self):
        for account_move in self:
            if account_move.move_type == 'out_invoice':
                pos_session = self.env['pos.session'].search([
                    ('global_invoice_id', '=', account_move.id)
                ], limit=1)
                if pos_session:
                    raise UserError(
                        _('You cannot delete this invoice, since the session %s of the '
                          'point of sale has it assigned') % (pos_session.name))
        return super(AccountMove, self).unlink()


