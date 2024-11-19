from datetime import date

from odoo import models, fields, _
from collections import defaultdict

from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero
import logging

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = 'pos.session'

    global_invoice_id = fields.Many2one(
        comodel_name="account.move",
        string="Global invoice",
        required=False,
    )

    global_invoice_payment_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Global invoice payment move",
        required=False,
    )

    has_global_invoice = fields.Boolean(
        string="Global invoiced",
    )
    apply_global_invoice = fields.Boolean(related="company_id.apply_global_invoice")

    def _check_session_can_be_invoiced(self, records):
        pos_journal = False
        global_customer = False
        for record in records:
            if not record.order_ids:
                raise UserError(_(
                    'The session number {} has no orders, please '.format(
                        record.name
                    )
                    + 'remove it from the invoicing list'
                ))
            if record.has_global_invoice:
                raise UserError(_(
                    'The session number {} has global invoice, please'.format(
                        record.name
                    )
                    + ' remove it from the invoicing list'
                ))
            if record.state != 'closed':
                raise UserError(_(
                    'The session number {} is not closed, please close'.format(
                        record.name
                    )
                    + ' this session or remove it from the invoicing list'
                ))
            global_customer = record.config_id.global_customer_id
            if not pos_journal:
                pos_journal = record.config_id.journal_id
            if pos_journal.id != record.config_id.journal_id.id:
                raise UserError(
                    _('All point of sales need to have the same journal to be invoiced '
                      'together, please set the same jornals for all point of sales'))
        return pos_journal, global_customer

    def _accumulate_amounts_global_invoice(self, data):
        # Accumulate the amounts for each accounting lines group
        # Each dict maps `key` -> `amounts`, where `key` is the group key.
        # E.g. `combine_receivables_bank` is derived from pos.payment records
        # in the self.order_ids with group key of the `payment_method_id`
        # field of the pos.payment record.
        amounts = lambda : {'amount': 0.0, 'amount_converted': 0.0}
        tax_amounts = lambda: {
            'amount': 0.0,
            'amount_converted': 0.0,
            'base_amount': 0.0,
            'base_amount_converted': 0.0
        }
        split_receivables_bank = defaultdict(amounts)
        split_receivables_cash = defaultdict(amounts)
        split_receivables_pay_later = defaultdict(amounts)
        combine_receivables_bank = defaultdict(amounts)
        combine_receivables_cash = defaultdict(amounts)
        combine_receivables_pay_later = defaultdict(amounts)
        combine_invoice_receivables = defaultdict(amounts)
        split_invoice_receivables = defaultdict(amounts)
        sales = defaultdict(amounts)
        taxes = defaultdict(tax_amounts)
        stock_expense = defaultdict(amounts)
        stock_return = defaultdict(amounts)
        stock_output = defaultdict(amounts)
        rounding_difference = {'amount': 0.0, 'amount_converted': 0.0}
        # Track the receivable lines of the order's invoice payment moves for
        # reconciliation
        # These receivable lines are reconciled to the corresponding invoice
        # receivable lines
        # of this session's move_id.
        combine_inv_payment_receivable_lines = defaultdict(
            lambda: self.env['account.move.line']
        )
        split_inv_payment_receivable_lines = defaultdict(
            lambda: self.env['account.move.line']
        )
        pos_receivable_account = (
            self.company_id.account_default_pos_receivable_account_id
        )
        currency_rounding = self.currency_id.rounding
        total_paid_orders = 0
        global_invoice_line = self.get_line_global(self.order_ids, "invoice")
        global_refund_line = self.get_line_global(self.order_ids, "refund")
        
        for order in self.order_ids:
            order_is_invoiced = order.is_invoiced
            for payment in order.payment_ids:
                amount = payment.amount
                if float_is_zero(
                    amount,
                    precision_rounding=currency_rounding
                ):
                    continue
                payment_date = payment.payment_date
                payment_method = payment.payment_method_id
                is_split_payment = (
                    payment.payment_method_id.split_transactions
                )
                payment_type = payment_method.type

                # If not pay_later, we create the receivable vals for both
                # invoiced and uninvoiced orders.
                # Separate the split and aggregated payments.
                # Moreover, if the order is invoiced, we create the pos
                # receivable vals that will balance the
                # pos receivable lines from the invoice payments.
                if payment_type != 'pay_later':
                    if is_split_payment and payment_type == 'cash':
                        split_receivables_cash[payment] = (
                            self._update_amounts(
                                split_receivables_cash[payment],
                                {'amount': amount},
                                payment_date
                            )
                        )
                    elif not is_split_payment and payment_type == 'cash':
                        combine_receivables_cash[payment_method] = (
                            self._update_amounts(
                                combine_receivables_cash[payment_method],
                                {'amount': amount},
                                payment_date
                            )
                        )
                    elif is_split_payment and payment_type == 'bank':
                        split_receivables_bank[payment] = (
                            self._update_amounts(
                                split_receivables_bank[payment],
                                {'amount': amount},
                                payment_date
                            )
                        )
                    elif not is_split_payment and payment_type == 'bank':
                        combine_receivables_bank[payment_method] = (
                            self._update_amounts(
                                combine_receivables_bank[payment_method],
                                {'amount': amount},
                                payment_date
                            )
                        )

                    # Create the vals to create the pos receivables that
                    # will balance the pos receivables from invoice
                    # payment moves.
                    if order_is_invoiced:
                        if is_split_payment:
                            split_inv_payment_receivable_lines[
                                payment
                            ] |= payment.account_move_id.line_ids.filtered(
                                lambda line: line.account_id == pos_receivable_account
                            )
                            split_invoice_receivables[payment] = (
                                self._update_amounts(
                                    split_invoice_receivables[payment],
                                    {'amount': payment.amount},
                                    order.date_order
                                )
                            )
                        else:
                            combine_inv_payment_receivable_lines[
                                payment_method
                            ] |= payment.account_move_id.line_ids.filtered(
                                lambda line: line.account_id == pos_receivable_account
                            )
                            combine_invoice_receivables[payment_method] = (
                                self._update_amounts(
                                    combine_invoice_receivables[
                                        payment_method
                                    ],
                                    {'amount': payment.amount},
                                    order.date_order
                                )
                            )

                # If pay_later, we create the receivable lines.
                #   if split, with partner
                #   Otherwise, it's aggregated (combined)
                # But only do if order is *not* invoiced because no
                # account move is created for pay later invoice payments.
                if payment_type == 'pay_later' and not order_is_invoiced:
                    if is_split_payment:
                        split_receivables_pay_later[payment] = (
                            self._update_amounts(
                                split_receivables_pay_later[payment],
                                {'amount': amount},
                                payment_date
                            )
                        )
                    elif not is_split_payment:
                        combine_receivables_pay_later[payment_method] = (
                            self._update_amounts(
                                combine_receivables_pay_later[
                                    payment_method
                                ],
                                {'amount': amount},
                                payment_date
                            )
                        )

            if not order_is_invoiced:
                order.partner_id._increase_rank('customer_rank')

        if self.company_id.anglo_saxon_accounting:
            global_session_pickings = self.picking_ids.filtered(
                lambda p: not p.pos_order_id
            )
            if global_session_pickings:
                stock_moves = self.env['stock.move'].sudo().search([
                    ('picking_id', 'in', global_session_pickings.ids),
                    ('company_id.anglo_saxon_accounting', '=', True),
                    (
                        'product_id.categ_id.property_valuation',
                        '=',
                        'real_time'
                    ),
                ])
                for move in stock_moves:
                    exp_key = move.product_id._get_product_accounts()[
                        'expense'
                    ]
                    categ = move.product_id.categ_id
                    out_key = categ.property_stock_account_output_categ_id
                    amount = -sum(
                        move.stock_valuation_layer_ids.mapped('value')
                    )
                    stock_expense[exp_key] = self._update_amounts(
                        stock_expense[exp_key],
                        {'amount': amount},
                        move.picking_id.date,
                        force_company_currency=True
                    )
                    if move.location_id.usage == 'customer':
                        stock_return[out_key] = self._update_amounts(
                            stock_return[out_key],
                            {'amount': amount},
                            move.picking_id.date,
                            force_company_currency=True
                        )
                    else:
                        stock_output[out_key] = self._update_amounts(
                            stock_output[out_key],
                            {'amount': amount},
                            move.picking_id.date,
                            force_company_currency=True
                        )
        
        MoveLine = self.env['account.move.line'].with_context(
            check_move_validity=False,
            skip_invoice_sync=True
        )
        data.update({
            'taxes': taxes,
            'sales': sales,
            'stock_expense': stock_expense,
            'split_receivables_bank': split_receivables_bank,
            'combine_receivables_bank': combine_receivables_bank,
            'split_receivables_cash': split_receivables_cash,
            'combine_receivables_cash': combine_receivables_cash,
            'combine_invoice_receivables': combine_invoice_receivables,
            'split_receivables_pay_later': split_receivables_pay_later,
            'combine_receivables_pay_later': combine_receivables_pay_later,
            'stock_return': stock_return,
            'stock_output': stock_output,
            'combine_inv_payment_receivable_lines': (
                combine_inv_payment_receivable_lines
            ),
            'rounding_difference': rounding_difference,
            'MoveLine': MoveLine,
            'invoice_lines': global_invoice_line,
            'refund_lines': global_refund_line,
            'total_paid_orders': total_paid_orders,
            'split_invoice_receivables': split_invoice_receivables,
            'split_inv_payment_receivable_lines': (
                split_inv_payment_receivable_lines
            ),
        })
        return data

    def get_line_global(self, order_ids, move_type):
        list_invoice_line_ids = []
        for order in order_ids.filtered(lambda x: not x.account_move):
            if move_type == "refund":
                order_line = order.lines.filtered(lambda self: self.qty < 0)
            else:
                order_line = order.lines.filtered(lambda self: self.qty > 0)
            for line in order_line:
                list_invoice_line_ids.append({
                    "name": (
                        'Ticket: '
                        + order.pos_reference
                        + " "
                        + line.full_product_name
                    ),
                    "product_id": line.product_id.id,
                    "quantity": abs(line.qty),
                    "discount": abs(line.discount),
                    "account_id": line.product_id.product_tmpl_id.get_product_accounts()['income'].id,
                    "price_unit": line.price_unit,
                    "tax_ids": line.tax_ids_after_fiscal_position.ids,
                })
        return list_invoice_line_ids

    def _validate_session(
        self,
        balancing_account=False,
        amount_to_balance=0,
        bank_payment_method_diffs=None
    ):
        res = super(PosSession, self)._validate_session(
            balancing_account,
            amount_to_balance,
            bank_payment_method_diffs
        )
        journal = self.config_id.journal_id
        if self.config_id.create_global_invoice:
            # Handle automatic invoicing (Same as manual till this point)
            if self.config_id.global_invoice_method == 'automatic':
                self.create_global_invoice(journal)
        return res

    def create_global_invoice(self, journal, bank_payment_method_diffs=None):
        # Check if all pos config have the same configuration
        account_move = self.env['account.move'].with_context(
            default_journal_id=journal.id
        ).create({
            'journal_id': journal.id,
            'date': fields.Date.context_today(self),
            'ref': self.name
        })
        
        if not self.config_id.invoice_journal_id:
            raise ValidationError("No esta configurado el diario para facturacion en este PdV")
        if not self.config_id.global_customer_id:
            raise ValidationError("No esta configurado el cliente publico general para facturacion global en este PdV")
        if not self.config_id.global_periodicity:
            raise ValidationError("No esta configurada la periodicidad para facturacion global en este PdV")

        global_invoice = self.env['account.move'].with_context(
            default_journal_id=self.config_id.invoice_journal_id.id
        ).create({
            'journal_id': self.config_id.invoice_journal_id.id,
            'date': fields.Date.context_today(self),
            'ref': self.name,
            'partner_id': self.config_id.global_customer_id.id,
            'move_type': 'out_invoice',
            'is_global_invoice': True,
            'periodicidad': self.config_id.global_periodicity
        })  

        self._set_references_global_invoice(
            self,
            global_invoice,
            account_move
        )
        self.create_values_in_data(
            global_invoice,
            account_move,
            self,
            bank_payment_method_diffs,
            
        )

        if global_invoice.line_ids:
            global_invoice._post()
            if global_invoice.line_ids and global_invoice.state == 'posted':
                global_customer = self.config_id.global_customer_id
                move_lines = self.env['account.move.line'].search([
                    ('move_id', 'in', (global_invoice.id, account_move.id)),
                    ('account_id', '=', global_customer.property_account_receivable_id.id),
                    ('name', '!=', 'From invoiced orders')
                ])
                move_lines.reconcile()

        self.write({'has_global_invoice': True})

        return {
            'name': _('Global invoice'),
            'view_mode': 'form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'res_id': global_invoice.id,
        }
    
    def dict_payments_data(self, order_ids):
        totales_dict = {}
        for rec in order_ids:
            payment = self.env['pos.payment'].search([
                ('pos_order_id', '=', rec.id)
            ])
            for pay in payment:
                if pay.payment_method_id.name in totales_dict:
                    totales_dict[pay.payment_method_id.name][0] += pay.amount
                else:
                    totales_dict[pay.payment_method_id.name] = [
                        pay.amount,
                        pay.payment_method_id.journal_id,
                        pay.payment_method_id.id
                    ]
        return totales_dict

    def create_values_in_data(
        self,
        global_invoice,
        global_invoice_payment_move,
        pos_session,
        bank_payment_method_diffs,
    ):
        data = {'bank_payment_method_diffs': bank_payment_method_diffs or {}}
        
        data = pos_session._accumulate_amounts_global_invoice(data)

        global_invoice_lines = data.get('invoice_lines')
        refund_product_lines = {}

        for line in data.get('refund_lines'):
            for gline in global_invoice_lines:
                if gline.get('product_id') == line.get('product_id') and gline.get('price_unit') == line.get('price_unit'):
                    gline['quantity'] -= line.get('quantity', 0)
                    break

            product_id = self.env['product.product'].browse(line.get('product_id'))
            income_account_id = product_id.categ_id.property_account_income_categ_id.id
            if income_account_id in refund_product_lines:
                refund_product_lines[income_account_id] += line.get('quantity') * line.get('price_unit')
            else:
                refund_product_lines[income_account_id] = line.get('quantity') * line.get('price_unit')

        global_invoice_lines = list(filter(lambda x: x.get('quantity') > 0, global_invoice_lines))
        global_invoice.write({'invoice_line_ids': [(
            0, None, invoice_line
        ) for invoice_line in global_invoice_lines]})
        dict_total = self.dict_payments_data(pos_session.order_ids.filtered(lambda x: not x.account_move))
        invoice_payment_lines = [] 

        for method, method_amount in dict_total.items():
            if method != "Prestavale":
                invoice_payment_lines.extend([
                        (0, 0, {
                            'name': f"Global Invoice payment - {global_invoice.ref} - {method}",
                            'account_id': pos_session.company_id.account_default_pos_receivable_account_id.id,  # Clientes nacionales POS
                            'debit': method_amount[0],
                            'partner_id':pos_session.config_id.global_customer_id.id,
                            'credit': 0,
                        }),
                        (0, 0, {
                            'name': f"Global Invoice payment - {global_invoice.ref} - {method}",
                            'account_id': pos_session.config_id.global_customer_id.property_account_receivable_id.id,  # Clientes nacionales
                            'debit': 0,
                            'credit': method_amount[0],
                            'partner_id':pos_session.config_id.global_customer_id.id,
                        }),
                    ]
                )

        for account_id, amount in refund_product_lines.items():
            invoice_payment_lines.append((0, 0, {
                'name': f'Refund - {account_id}',
                'account_id': account_id,
                'debit': amount,
                'credit': 0,
                'partner_id':pos_session.config_id.global_customer_id.id,
            }))
            invoice_payment_lines.append((0, 0, {
                'name': f'Sales - {account_id}',
                'account_id': account_id,
                'debit': 0,
                'credit': amount,
                'partner_id':pos_session.config_id.global_customer_id.id,
            }))

        global_invoice_payment_move.write({
            'line_ids': invoice_payment_lines,
        })
        global_invoice_payment_move._post()
        return data

    def _set_references_global_invoice(
        self,
        pos_session,
        global_invoice,
        global_invoice_payment_move
    ):
        ref_global = (
            (global_invoice.ref + ' | ') if global_invoice.ref else ''
        )
        global_invoice.write({
            'ref': ref_global + pos_session.name
        })
        global_invoice_payment_move.write({
            'ref': f'{global_invoice.ref} - Global payment',
        })
        pos_session.write({
            'global_invoice_id': global_invoice.id,
            'global_invoice_payment_move_id': global_invoice_payment_move,
        })

    def create_manual_global_invoice(self, records_multi):
        for records in records_multi:
            # Check if all pos config have the same configuration
            self._check_session_can_be_invoiced(
                records
            )
            global_journal = records.config_id.global_journal_id
            
            if not global_journal:
                raise ValidationError("No esta configurado el diario para facturacion global en este PdV '%s'" % records.config_id.name)
            if not records.config_id.global_customer_id:
                raise ValidationError("No esta configurado el cliente global para facturacion global en este PdV '%s'" % records.config_id.name)
            if not records.config_id.global_periodicity:
                raise ValidationError("No esta configurada la periodicidad para facturacion global en este PdV '%s'" % records.config_id.name)

            global_invoice = self.env['account.move'].with_context(
                default_journal_id=global_journal.id
            ).create({
                'journal_id': global_journal.id,
                'date': fields.Date.context_today(self),
                'invoice_payment_term_id': self.env.ref("account.account_payment_term_45days").id,
                'ref': '',
                'partner_id': records.config_id.global_customer_id.id,
                'move_type': 'out_invoice',
                'is_global_invoice': True,
                'periodicidad': records.config_id.global_periodicity,
                'l10n_mx_edi_usage': 'S01'
            })

            global_invoice_payment_move = self.env['account.move'].create({
                'ref': f'{global_invoice.ref} - payment',
                'journal_id': records.config_id.journal_id.id,
                'date': global_invoice.date,
            })

            records.move_id.button_draft()
            records.move_id.unlink()

            for order_id in self.order_ids.filtered(
                lambda self: not self.account_move
            ):
                order_id.write({
                    'account_move': global_invoice.id,
                    'state': 'invoiced'
                })

            for pos_session in records:
                self._set_references_global_invoice(
                    pos_session,
                    global_invoice,
                    global_invoice_payment_move
                )
                self.create_values_in_data(
                    global_invoice,
                    global_invoice_payment_move,
                    pos_session,
                    None
                )

            if global_invoice.line_ids:
                global_invoice._post()
                if global_invoice.line_ids and global_invoice.state == 'posted':
                    global_customer = records.config_id.global_customer_id
                    move_lines = self.env['account.move.line'].search([
                        ('move_id', 'in', (global_invoice.id, global_invoice_payment_move.id)),
                        ('account_id', '=', global_customer.property_account_receivable_id.id),
                        ('name','!=', f'Global Invoice payment - {global_invoice.ref} - Prestavale')
                    ])
                    move_lines.reconcile()
            else:
                raise ValidationError(_("No hay lineas para la factura global es posible que la sesion '%s' no tenga ordenes sin facturar" % records.name))
            records.write({'has_global_invoice': True})

    def _reconcile_account_move_lines_stock(self, data):
        stock_output_lines = data.get('stock_output_lines')
        # reconcile stock output lines
        try:
            pickings = self.picking_ids.filtered(lambda p: not p.pos_order_id)
            pickings |= self.order_ids.filtered(
                lambda o: not o.is_invoiced
            ).mapped('picking_ids')
            stock_moves = self.env['stock.move'].search([
                ('picking_id', 'in', pickings.ids)
            ])
            stock_account_move_lines = self.env['account.move'].search(
                [('stock_move_id', 'in', stock_moves.ids)]).mapped('line_ids')
            for account_id in stock_output_lines:
                (stock_output_lines[account_id]
                 | stock_account_move_lines.filtered(
                    lambda aml: aml.account_id == account_id
                )).filtered(lambda aml: not aml.reconciled)._post()
            for account_id in stock_output_lines:
                (stock_output_lines[account_id]
                 | stock_account_move_lines.filtered(
                    lambda aml: aml.account_id == account_id
                )).filtered(lambda aml: not aml.reconciled).reconcile()
        except:
            pass
        return data

    def _reconcile_account_move_lines(self, data):
        data = super(PosSession, self)._reconcile_account_move_lines(data)
        combine_inv_payment_receivable_lines = data.get(
            'combine_inv_payment_receivable_lines'
        )
        split_inv_payment_receivable_lines = data.get(
            'split_inv_payment_receivable_lines'
        )
        combine_invoice_receivable_lines = data.get(
            'combine_invoice_receivable_lines'
        )
        split_invoice_receivable_lines = data.get(
            'split_invoice_receivable_lines'
        )
        try:
            account = self.company_id.account_default_pos_receivable_account_id
            if account.reconcile:
                for payment_method in combine_inv_payment_receivable_lines:
                    lines = combine_inv_payment_receivable_lines[
                        payment_method
                    ] | combine_invoice_receivable_lines.get(
                        payment_method,
                        self.env['account.move.line']
                    )
                    lines.filtered(
                        lambda line: not line.reconciled
                    ).reconcile()

                for payment in split_inv_payment_receivable_lines:
                    lines = split_inv_payment_receivable_lines[
                        payment
                    ] | split_invoice_receivable_lines.get(
                        payment,
                        self.env['account.move.line']
                    )
                    lines.filtered(
                        lambda line: not line.reconciled
                    ).reconcile()
        except:
            pass

        return data

    def _prepare_balancing_line_vals(self, imbalance_amount, move):
        account = self._get_balancing_account()
        partial_vals = {
            'name': _('Difference at closing PoS session'),
            'account_id': account.id,
            'move_id': move.id,
            'partner_id': self.config_id.global_customer_id.id,
        }
        # `imbalance_amount` is already in terms of company currency so it is
        # the amount_converted
        # param when calling `_credit_amounts`. amount param will be the
        # converted value of
        # `imbalance_amount` from company currency to the session currency.
        imbalance_amount_session = 0
        if not self.is_in_company_currency:
            imbalance_amount_session = self.company_id.currency_id._convert(
                imbalance_amount,
                self.currency_id,
                self.company_id,
                fields.Date.context_today(self)
            )
        return self._credit_amounts(
            partial_vals,
            imbalance_amount_session,
            imbalance_amount
        )

    def _get_related_account_moves(self):
        res = super(PosSession, self)._get_related_account_moves()
        global_invoice = self.mapped("global_invoice_id")
        global_invoice_payment_move = self.mapped("global_invoice_payment_move_id")

        return res | global_invoice | global_invoice_payment_move
