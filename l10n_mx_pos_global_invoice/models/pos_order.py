from odoo import fields, models, _,api
from odoo.exceptions import UserError


class PosOrder(models.Model):
    _inherit = "pos.order"

    refund_field = fields.Boolean()

    global_periodicity_field = fields.Selection(
        string="Periodicidad",
        selection=[
            ('01', 'Diario'),
            ('02', 'Semanal'),
            ('03', 'Quincenal'),
            ('04', 'Mensual'),
            ('05', 'Bimestral'),
        ]
    )

    global_order_cfdi_month = fields.Selection(
        string="c_Meses",
        selection=[
            ('01', 'Enero'),
            ('02', 'Febrero'),
            ('03', 'Marzo'),
            ('04', 'Abril'),
            ('05', 'Mayo'),
            ('06', 'Junio'),
            ('07', 'Julio'),
            ('08', 'Agosto'),
            ('09', 'Septiembre'),
            ('10', 'Octubre'),
            ('11', 'Noviembre'),
            ('12', 'Diciembre'),
            ('13', 'Enero - Febrero'),
            ('14', 'Marzo - Abril'),
            ('15', 'Mayo - Junio'),
            ('16', 'Julio - Agosto'),
            ('17', 'Septiembre - Octubre'),
            ('18', 'Noviembre - Diciembre'),
        ]
    )

    def _prepare_global_invoice_line(self, order_line):
        return {
            'product_id': order_line.product_id.id,
            'quantity': order_line.qty,
            'discount': order_line.discount,
            'price_unit': order_line.price_unit,
            'name': order_line.full_product_name or order_line.product_id.display_name,
            'tax_ids': [(6, 0, order_line.tax_ids_after_fiscal_position.ids)],
            'product_uom_id': order_line.product_uom_id.id,
        }

    def _prepare_refund_values(self, current_session):
        self.ensure_one()

        return {
            'name': self.name + _(' REFUND'),
            'session_id': current_session.id,
            'date_order': fields.Datetime.now(),
            'pos_reference': self.pos_reference,
            'lines': False,
            'amount_tax': -self.amount_tax,
            'amount_total': -self.amount_total,
            'amount_paid': 0,
            'refund_field': True
        }

    def refund(self):
        """Create a copy of order  for refund order"""
        refund_orders = self.env['pos.order']
        for order in self:
            # When a refund is performed, we are creating it in a session having the same config as the original
            # order. It can be the same session, or if it has been closed the new one that has been opened.
            current_session = order.session_id.config_id.current_session_id
            #if not current_session:
             #   raise UserError(_('To return product(s), you need to open a session in the POS %s', order.session_id.config_id.display_name))
            refund_order = order.copy(
                order._prepare_refund_values(current_session)
            )
            for line in order.lines:
                PosOrderLineLot = self.env['pos.pack.operation.lot']
                for pack_lot in line.pack_lot_ids:
                    PosOrderLineLot += pack_lot.copy()
                line.copy(line._prepare_refund_data(refund_order, PosOrderLineLot))
            refund_orders |= refund_order
            order.refund_field = True
        return {
            'name': _('Return Products'),
            'view_mode': 'form',
            'res_model': 'pos.order',
            'res_id': refund_orders.ids[0],
            'view_id': False,
            'context': self.env.context,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
    @api.onchange("refund_field")
    def actualizar(self):
        for order in self:
            for line in order.lines:
                line._actualizar_qty()

class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    def _actualizar_qty(self):
        for r in self:
            es_producto = r.order_id.lines.refund_orderline_ids.order_id.lines.full_product_name
            if es_producto == r.full_product_name :
                r.refunded_qty = -sum(r.mapped('refund_orderline_ids.qty'))
                qty = r.qty - r.refunded_qty
                r.qty = qty