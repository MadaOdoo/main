from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)


   


class account_payment(models.Model):
    _inherit = 'account.payment'
    
    invoice_lines = fields.One2many('payment.invoice.line', 'payment_id', string="Invoice Line")
    multipagos = fields.Boolean(
        string='Multipagos', default=True
    )
    skip_reconcile  = fields.Boolean(
        string='Saltar la conciliacion',
        help='Se postea el pago pero las lineas de las facturas implicadas tendran que conciliarse de forma externa'
    )
    is_all_reconcile  = fields.Boolean(
        string='Completamente conciliado'
    )

    def get_lines_ids(self):
        print("------get_lines_ids-------")
        for rec in self:
            if rec.line_ids:
                rec.line_ids.unlink()
   
    def update_invoice_lines(self):
        for rec in self:
            if rec.payment_type == 'inbound':
                rec.get_lines_ids()
                for inv in rec.invoice_lines:
                    inv.open_amount = inv.invoice_id.amount_residual 
            rec.onchange_partner_id()
        
    # def action_draft(self):
    #     for rec in self:
    #         moves = rec.mapped('move_line_ids.move_id')
    #         moves.filtered(lambda move: move.state == 'posted').button_draft()
    #         moves.with_context(force_delete=True).unlink()
    #         rec.write({'state': 'draft','name':False,'move_name':''})

    def clean_lines_invoices(self):
        for rec in self:
            if rec.invoice_lines:
                for line in rec.invoice_lines:
                    if line.check_line == False:
                        line.unlink()

    def line_value(self):
        for rec in self:
            if rec.invoice_lines:
                amount = 0
                for line in rec.invoice_lines:
                    amount += line.allocation
                val = round(amount,2)
                if val != rec.amount:
                    print("+++++++++++")
                    #raise UserError(_("El total de las lineas excede el total del pago %s.", amount))

    def clean_lines(self):
        for rec in self:
            if rec.invoice_lines:
                for line in rec.invoice_lines:
                    if line.allocation == 0.0:
                        line.unlink()

    def action_post(self):
        # OVERRIDE
        res = super().action_post()
        for rec in self:
            if rec.is_internal_transfer == False:
                rec.line_value()
                rec.clean_lines()
                if not rec.skip_reconcile:
                    rec.multipay()
        return res
    
    def _cron_auto_reconcile_lines(self, batch_size=None):
        domain = [('skip_reconcile', '=', True), ('state', '=', 'posted'), ('is_all_reconcile', '=', False)]
        payment = self.env['account.payment'].search(domain, limit=1, order='id')
        if payment:
            pay_move_lines = payment.move_id.line_ids.filtered(lambda x: x.invoice_id and (x.credit or x.debit) and not x.reconciled)
            if pay_move_lines:
                _logger.info('El pago {} con id {} tiene {} lineas por conciliar'.format(payment.name, payment.id, len(pay_move_lines)))
                lote = pay_move_lines[:batch_size]
                _logger.info('Conciliando un lote de {} lineas'.format(len(lote)))
                for aml in lote:
                    pil = payment.invoice_lines.filtered(lambda l: l.invoice_id.id == aml.invoice_id.id)
                    lines = pil.invoice_line_id + aml
                    payment.move_id.js_assign_outstanding_lines(lines)
                _logger.info('Las {} lineas fueron Conciliadas'.format(len(lote)))
                if len(pay_move_lines[:batch_size]) == len(pay_move_lines):
                    payment.is_all_reconcile = True
                    _logger.info('El pago ya no tiene mas lineas para conciliar'.format(payment.name))
            else: 
                payment.is_all_reconcile = True
                _logger.info('El pago ya no tiene mas lineas para conciliar'.format(payment.name))
        else:
            _logger.info('No hay pagos candidatos a realizarle auto conciliacion')

    @api.onchange('partner_id', 'currency_id')
    def onchange_partner_id(self):
        # if self.payment_type == 'inbound':
            # if self.partner_id and self.payment_type != 'transfer' and self.multipagos == True:
        if self.partner_id and self.multipagos == True:
            vals = {}
            line = [(6, 0, [])]
            invoice_ids = []
            if self.payment_type == 'outbound' and self.partner_type == 'supplier':
                invoice_ids = self.env['account.move'].search([('partner_id', 'in', [self.partner_id.id]),
                                                                  ('state', '=','posted'),
                                                                  ('amount_residual','>',0.0),
                                                                  ('move_type','=', 'in_invoice'),
                                                                  ('currency_id', '=', self.currency_id.id),
                                                                  ('pago', '=', True)])

            if self.payment_type == 'inbound' and self.partner_type == 'supplier':
                invoice_ids = self.env['account.move'].search([('partner_id', 'in', [self.partner_id.id]),
                                                                  ('state', '=','posted'),
                                                                  ('amount_residual','>',0.0),
                                                                  ('move_type','=', 'in_invoice'),
                                                                  ('currency_id', '=', self.currency_id.id),
                                                                  ('pago', '=', True)])

            if self.payment_type == 'inbound' and self.partner_type == 'customer':
                invoice_ids = self.env['account.move'].search([('partner_id', 'in', [self.partner_id.id]),
                                                                  ('state', '=','posted'),
                                                                  ('amount_residual','>',0.0),
                                                                  ('move_type','=', 'out_invoice'),
                                                                  ('currency_id', '=', self.currency_id.id),
                                                                  ('pago', '=', True)])

            if self.payment_type == 'outbound' and self.partner_type == 'customer':
                invoice_ids = self.env['account.move'].search([('partner_id', 'in', [self.partner_id.id]),
                                                                  ('state', '=','posted'),
                                                                  ('amount_residual','>',0.0),
                                                                  ('move_type','=', 'out_invoice'),
                                                                  ('currency_id', '=', self.currency_id.id),
                                                                  ('pago', '=', True)])

            for inv in invoice_ids[::-1]:
                vals = {
                       'invoice_id': inv.id,
                       }
                
                line.append((0, 0, vals))
            self.invoice_lines = line
            #self.btn_calcular_lines_amount()
        # if self.partner_id and self.payment_type != 'transfer' and self.multipagos == False:
        if self.partner_id and self.multipagos == False:
            vals = {}
            line = [(6, 0, [])]
            invoice_ids = []
            if self.payment_type == 'outbound' and self.partner_type == 'supplier':
                invoice_ids = self.env['account.move'].search([('name', '=', self.communication)])

            if self.payment_type == 'inbound' and self.partner_type == 'supplier':
                invoice_ids = self.env['account.move'].search([('name', '=', self.communication)])

            if self.payment_type == 'inbound' and self.partner_type == 'customer':
                invoice_ids = self.env['account.move'].search([('name', '=', self.communication)])

            if self.payment_type == 'outbound' and self.partner_type == 'customer':
                invoice_ids = self.env['account.move'].search([('name', '=', self.communication)])

            for inv in invoice_ids[::-1]:
                vals = {
                       'invoice_id': inv.id,
                       }
                
                line.append((0, 0, vals))
            self.invoice_lines = line
            #self.btn_calcular_lines_amount()

# #we could add another line with a comparation between amount_residual > 0
#     @api.onchange('partner_id', 'currency_id')
#     def onchange_partner_id(self):
#         print("------onchange_partner_id-------")
#         if self.payment_type == 'inbound':
#             if self.partner_id and self.payment_type != 'transfer' and self.multipagos == True:
#                 vals = {}
#                 line = [(6, 0, [])]
#                 invoice_ids = []
#                 if self.payment_type == 'outbound' and self.partner_type == 'supplier':
#                     invoice_ids = self.env['account.move'].search([('partner_id', 'in', [self.partner_id.id]),
#                                                                       ('state', '=','posted'),
#                                                                       ('amount_residual','>',0.0),
#                                                                       ('move_type','=', 'in_invoice'),
#                                                                       ('currency_id', '=', self.currency_id.id)])

#                 if self.payment_type == 'inbound' and self.partner_type == 'supplier':
#                     invoice_ids = self.env['account.move'].search([('partner_id', 'in', [self.partner_id.id]),
#                                                                       ('state', '=','posted'),
#                                                                       ('amount_residual','>',0.0),
#                                                                       ('move_type','=', 'in_invoice'),
#                                                                       ('currency_id', '=', self.currency_id.id)])

#                 if self.payment_type == 'inbound' and self.partner_type == 'customer':
#                     invoice_ids = self.env['account.move'].search([('partner_id', 'in', [self.partner_id.id]),
#                                                                       ('state', '=','posted'),
#                                                                       ('amount_residual','>',0.0),
#                                                                       ('move_type','=', 'out_invoice'),
#                                                                       ('currency_id', '=', self.currency_id.id)])

#                 if self.payment_type == 'outbound' and self.partner_type == 'supplier':
#                     invoice_ids = self.env['account.move'].search([('partner_id', 'in', [self.partner_id.id]),
#                                                                       ('state', '=','posted'),
#                                                                       ('amount_residual','>',0.0),
#                                                                       ('move_type','=', 'out_refund'),
#                                                                       ('currency_id', '=', self.currency_id.id)])
#                 print("INVOICES: ", invoice_ids)
#                 for inv in invoice_ids[::-1]:
#                     vals = {
#                            'invoice_id': inv.id,
#                            }
                    
#                     line.append((0, 0, vals))
#                 self.invoice_lines = line
#                 self.onchnage_amount()
#             if self.partner_id and self.payment_type != 'transfer' and self.multipagos == False:
#                 vals = {}
#                 line = [(6, 0, [])]
#                 invoice_ids = []
#                 if self.payment_type == 'outbound' and self.partner_type == 'supplier':
#                     invoice_ids = self.env['account.move'].search([('name', '=', self.communication)])

#                 if self.payment_type == 'inbound' and self.partner_type == 'supplier':
#                     invoice_ids = self.env['account.move'].search([('name', '=', self.communication)])

#                 if self.payment_type == 'inbound' and self.partner_type == 'customer':
#                     invoice_ids = self.env['account.move'].search([('name', '=', self.communication)])

#                 if self.payment_type == 'outbound' and self.partner_type == 'customer':
#                     invoice_ids = self.env['account.move'].search([('name', '=', self.communication)])

#                 for inv in invoice_ids[::-1]:
#                     vals = {
#                            'invoice_id': inv.id,
#                            }
                    
#                     line.append((0, 0, vals))
#                 self.invoice_lines = line
#                 self.onchnage_amount()
#         # if self.payment_type == 'outbound':
        
    
    @api.onchange('invoice_lines')
    def onchnage_invoice_lines(self):
        self.amount = sum(self.invoice_lines.mapped("allocation"))

    def multipay(self):
        invoice_lines = self.mapped('invoice_lines')
        if invoice_lines:
            for line in invoice_lines:
                lines = line.invoice_line_id
                if lines:
                    move_lines = self.move_id.line_ids.filtered(lambda lin: lin.invoice_id.id == line.invoice_id.id)
                    if move_lines:
                        if self.partner_type == 'customer':
                            lines += move_lines.filtered(lambda lin: lin.credit > 0)
                        elif self.partner_type == 'supplier':
                            lines += move_lines.filtered(lambda lin: lin.debit > 0)
                        self.move_id.js_assign_outstanding_lines(lines)

    # def _prepare_move_line_default_vals(self, write_off_line_vals=None):
    #     ''' Prepare the dictionary to create the default account.move.lines for the current payment.
    #     :param write_off_line_vals: Optional list of dictionaries to create a write-off account.move.line easily containing:
    #         * amount:       The amount to be added to the counterpart amount.
    #         * name:         The label to set on the line.
    #         * account_id:   The account on which create the write-off.
    #     :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
    #     '''
    #     self.ensure_one()
    #     write_off_line_vals = write_off_line_vals or {}

    #     if not self.outstanding_account_id:
    #         raise UserError(_(
    #             "You can't create a new payment without an outstanding payments/receipts account set either on the company or the %s payment method in the %s journal.",
    #             self.payment_method_line_id.name, self.journal_id.display_name))

    #     # Compute amounts.
    #     write_off_line_vals_list = write_off_line_vals or []
    #     write_off_amount_currency = sum(x['amount_currency'] for x in write_off_line_vals_list)
    #     write_off_balance = sum(x['balance'] for x in write_off_line_vals_list)

    #     if self.payment_type == 'inbound':
    #         # Receive money.
    #         liquidity_amount_currency = self.amount
    #     elif self.payment_type == 'outbound':
    #         # Send money.
    #         liquidity_amount_currency = -self.amount
    #     else:
    #         liquidity_amount_currency = 0.0

    #     liquidity_balance = self.currency_id._convert(
    #         liquidity_amount_currency,
    #         self.company_id.currency_id,
    #         self.company_id,
    #         self.date,
    #     )
    #     counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
    #     counterpart_balance = -liquidity_balance - write_off_balance
    #     currency_id = self.currency_id.id

    #     # Compute a default label to set on the journal items.
    #     liquidity_line_name = ''.join(x[1] for x in self._get_liquidity_aml_display_name_list())
    #     counterpart_line_name = ''.join(x[1] for x in self._get_counterpart_aml_display_name_list())

    #     line_vals_list = [
    #         # Liquidity line.
    #         {
    #             'name': liquidity_line_name,
    #             'date_maturity': self.date,
    #             'amount_currency': liquidity_amount_currency,
    #             'currency_id': currency_id,
    #             'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
    #             'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
    #             'partner_id': self.partner_id.id,
    #             'account_id': self.outstanding_account_id.id,
    #         },
    #         # Receivable / Payable.
    #         {
    #             'name': counterpart_line_name,
    #             'date_maturity': self.date,
    #             'amount_currency': counterpart_amount_currency,
    #             'currency_id': currency_id,
    #             'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
    #             'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
    #             'partner_id': self.partner_id.id,
    #             'account_id': self.destination_account_id.id,
    #         },
    #     ]
    #     print("+++ 316  +++",line_vals_list )
    #     print("+++ 317  +++",write_off_line_vals_list )
    #     return line_vals_list + write_off_line_vals_list

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        ''' Prepare the dictionary to create the default account.move.lines for the current payment.
        :param write_off_line_vals: Optional dictionary to create a write-off account.move.line easily containing:
            * amount:       The amount to be added to the counterpart amount.
            * name:         The label to set on the line.
            * account_id:   The account on which create the write-off.
        :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
        '''
        for rec in self:
            if rec.invoice_lines:
                print("++   330 ++")
                write_off_line_vals = write_off_line_vals or {}

                if not self.outstanding_account_id:
                    raise UserError(_(
                        "You can't create a new payment without an outstanding payments/receipts account set either on the company or the %s payment method in the %s journal.",
                        self.payment_method_line_id.name, self.journal_id.display_name))

                # Compute amounts.
                write_off_line_vals_list = write_off_line_vals or []
                write_off_amount_currency = sum(x['amount_currency'] for x in write_off_line_vals_list)
                write_off_balance = sum(x['balance'] for x in write_off_line_vals_list)

                if self.payment_type == 'inbound':
                    # Receive money.
                    liquidity_amount_currency = self.amount
                elif self.payment_type == 'outbound':
                    # Send money.
                    liquidity_amount_currency = -self.amount
                else:
                    liquidity_amount_currency = 0.0

                liquidity_balance = self.currency_id._convert(
                    liquidity_amount_currency,
                    self.company_id.currency_id,
                    self.company_id,
                    self.date,
                )
                counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
                counterpart_balance = -liquidity_balance - write_off_balance
                currency_id = self.currency_id.id

                # Compute a default label to set on the journal items.
                liquidity_line_name = ''.join(x[1] for x in self._get_liquidity_aml_display_name_list())
                counterpart_line_name = ''.join(x[1] for x in self._get_counterpart_aml_display_name_list())

                line_vals_list = [
                    # Liquidity line.
                    {
                        'name': liquidity_line_name,
                        'date_maturity': self.date,
                        'amount_currency': liquidity_amount_currency,
                        'currency_id': currency_id,
                        'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                        'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                        'partner_id': self.partner_id.id,
                        'account_id': self.outstanding_account_id.id,
                    },
                    # # Receivable / Payable.
                    # {
                    #     'name': counterpart_line_name,
                    #     'date_maturity': self.date,
                    #     'amount_currency': counterpart_amount_currency,
                    #     'currency_id': currency_id,
                    #     'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                    #     'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                    #     'partner_id': self.partner_id.id,
                    #     'account_id': self.destination_account_id.id,
                    # },
                ]
                for line in rec.invoice_lines:

                    if self.payment_type == 'inbound':
                    # Receive money.
                        liquidity_amount_currency = line.allocation
                    elif self.payment_type == 'outbound':
                        # Send money.
                        liquidity_amount_currency = -line.allocation
                    else:
                        liquidity_amount_currency = 0.0

                    liquidity_balance = self.currency_id._convert(
                        liquidity_amount_currency,
                        self.company_id.currency_id,
                        self.company_id,
                        self.date,
                    )
                    counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
                    counterpart_balance = -liquidity_balance - write_off_balance
                    currency_id = self.currency_id.id

                    # Compute a default label to set on the journal items.
                    liquidity_line_name = ''.join(x[1] for x in self._get_liquidity_aml_display_name_list())
                    counterpart_line_name = ''.join(x[1] for x in self._get_counterpart_aml_display_name_list())

                    line_vals_list.append({
                        'name': counterpart_line_name,
                        'date_maturity': self.date,
                        'amount_currency': counterpart_amount_currency,
                        'currency_id': currency_id,
                        'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                        'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                        'partner_id': self.partner_id.id,
                        'account_id': self.destination_account_id.id,
                        'invoice_id': line.invoice_id.id
                    })
                print("++   425 ++",line_vals_list)
                print("++   426 ++",write_off_line_vals_list)
                v = line_vals_list
                return line_vals_list + write_off_line_vals_list
            else:
                write_off_line_vals = write_off_line_vals or {}

                if not self.outstanding_account_id:
                    raise UserError(_(
                        "You can't create a new payment without an outstanding payments/receipts account set either on the company or the %s payment method in the %s journal.",
                        self.payment_method_line_id.name, self.journal_id.display_name))

                # Compute amounts.
                write_off_line_vals_list = write_off_line_vals or []
                write_off_amount_currency = sum(x['amount_currency'] for x in write_off_line_vals_list)
                write_off_balance = sum(x['balance'] for x in write_off_line_vals_list)

                if self.payment_type == 'inbound':
                    # Receive money.
                    liquidity_amount_currency = self.amount
                elif self.payment_type == 'outbound':
                    # Send money.
                    liquidity_amount_currency = -self.amount
                else:
                    liquidity_amount_currency = 0.0

                liquidity_balance = self.currency_id._convert(
                    liquidity_amount_currency,
                    self.company_id.currency_id,
                    self.company_id,
                    self.date,
                )
                counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
                counterpart_balance = -liquidity_balance - write_off_balance
                currency_id = self.currency_id.id

                # Compute a default label to set on the journal items.
                liquidity_line_name = ''.join(x[1] for x in self._get_liquidity_aml_display_name_list())
                counterpart_line_name = ''.join(x[1] for x in self._get_counterpart_aml_display_name_list())

                line_vals_list = [
                    # Liquidity line.
                    {
                        'name': liquidity_line_name,
                        'date_maturity': self.date,
                        'amount_currency': liquidity_amount_currency,
                        'currency_id': currency_id,
                        'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                        'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                        'partner_id': self.partner_id.id,
                        'account_id': self.outstanding_account_id.id,
                    },
                    # Receivable / Payable.
                    {
                        'name': counterpart_line_name,
                        'date_maturity': self.date,
                        'amount_currency': counterpart_amount_currency,
                        'currency_id': currency_id,
                        'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                        'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                        'partner_id': self.partner_id.id,
                        'account_id': self.destination_account_id.id,
                    },
                ]
                return line_vals_list + write_off_line_vals_list

     # -------------------------------------------------------------------------
    # SYNCHRONIZATION account.payment <-> account.move
    # -------------------------------------------------------------------------

    def _synchronize_from_moves(self, changed_fields):
        ''' Update the account.payment regarding its related account.move.
        Also, check both models are still consistent.
        :param changed_fields: A set containing all modified fields on account.move.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return

        for pay in self.with_context(skip_account_move_synchronization=True):

            # After the migration to 14.0, the journal entry could be shared between the account.payment and the
            # account.bank.statement.line. In that case, the synchronization will only be made with the statement line.
            if pay.move_id.statement_line_id:
                continue

            move = pay.move_id
            move_vals_to_write = {}
            payment_vals_to_write = {}

            if 'journal_id' in changed_fields:
                if pay.journal_id.type not in ('bank', 'cash'):
                    raise UserError(_("A payment must always belongs to a bank or cash journal."))

            if 'line_ids' in changed_fields:
                all_lines = move.line_ids
                liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

                if len(liquidity_lines) != 1:
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "include one and only one outstanding payments/receipts account.",
                        move.display_name,
                    ))

                # if len(counterpart_lines) != 1:
                #     raise UserError(_(
                #         "Journal Entry %s is not valid. In order to proceed, the journal items must "
                #         "include one and only one receivable/payable account (with an exception of "
                #         "internal transfers).",
                #         move.display_name,
                #     ))

                if any(line.currency_id != all_lines[0].currency_id for line in all_lines):
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "share the same currency.",
                        move.display_name,
                    ))

                if any(line.partner_id != all_lines[0].partner_id for line in all_lines):
                    raise UserError(_(
                        "Journal Entry %s is not valid. In order to proceed, the journal items must "
                        "share the same partner.",
                        move.display_name,
                    ))

                if counterpart_lines.account_id.account_type == 'asset_receivable':
                    partner_type = 'customer'
                else:
                    partner_type = 'supplier'

                liquidity_amount = liquidity_lines.amount_currency

                move_vals_to_write.update({
                    'currency_id': liquidity_lines.currency_id.id,
                    'partner_id': liquidity_lines.partner_id.id,
                })
                payment_vals_to_write.update({
                    'amount': abs(liquidity_amount),
                    'partner_type': partner_type,
                    'currency_id': liquidity_lines.currency_id.id,
                    'destination_account_id': counterpart_lines.account_id.id,
                    'partner_id': liquidity_lines.partner_id.id,
                })
                if liquidity_amount > 0.0:
                    payment_vals_to_write.update({'payment_type': 'inbound'})
                elif liquidity_amount < 0.0:
                    payment_vals_to_write.update({'payment_type': 'outbound'})

            move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
            pay.write(move._cleanup_write_orm_values(pay, payment_vals_to_write))

    def _synchronize_to_moves(self, changed_fields):
        ''' Update the account.move regarding the modified account.payment.
        :param changed_fields: A list containing all modified fields on account.payment.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return

        if not any(field_name in changed_fields for field_name in self._get_trigger_fields_to_synchronize()):
            return

        for pay in self.with_context(skip_account_move_synchronization=True):
            liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()

            # Make sure to preserve the write-off amount.
            # This allows to create a new payment with custom 'line_ids'.

            write_off_line_vals = []
            if liquidity_lines and counterpart_lines and writeoff_lines:
                write_off_line_vals.append({
                    'name': writeoff_lines[0].name,
                    'account_id': writeoff_lines[0].account_id.id,
                    'partner_id': writeoff_lines[0].partner_id.id,
                    'currency_id': writeoff_lines[0].currency_id.id,
                    'amount_currency': sum(writeoff_lines.mapped('amount_currency')),
                    'balance': sum(writeoff_lines.mapped('balance')),
                })

            line_vals_list = pay._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)
            line_ids_commands = []
            # _logger.error("="*50)
            # _logger.error(line_vals_list[0:2])
            # _logger.error(line_vals_list[2:])
            # _logger.error(liquidity_lines)
            # _logger.error(sum(liquidity_lines.mapped('debit')))
            # _logger.error(sum(liquidity_lines.mapped('credit')))
            # _logger.error(counterpart_lines)
            # _logger.error(sum(counterpart_lines.mapped('debit')))
            # _logger.error(sum(counterpart_lines.mapped('credit')))
            # _logger.error(writeoff_lines)
            if pay.move_id.line_ids:
                pay.move_id.write({'line_ids':[(5,)]})
            # # for liquidity_line in liquidity_lines:
            # #     line_ids_commands.append(Command.update(liquidity_line.id, line_vals_list[0]))
            # # if not liquidity_lines:
            # #     line_ids_commands.append(Command.create(line_vals_list[0]))
            # # for counterpart_line in counterpart_lines:
            # #     line_ids_commands.append(Command.update(counterpart_line.id, line_vals_list[1]))
            # # if not counterpart_lines:
            # #     line_ids_commands.append(Command.create(line_vals_list[1]))
            # # for line in writeoff_lines:
            # #     line_ids_commands.append((2, line.id))

            for line_vals in line_vals_list:
                if line_vals["debit"] or line_vals["credit"]:
                    line_ids_commands.append((0, 0, line_vals))

            # Update the existing journal items.
            # If dealing with multiple write-off lines, they are dropped and a new one is generated.

            pay.move_id.write({
                'partner_id': pay.partner_id.id,
                'currency_id': pay.currency_id.id,
                'partner_bank_id': pay.partner_bank_id.id,
                'line_ids': line_ids_commands,
            })

    def _create_paired_internal_transfer_payment(self):
        ''' When an internal transfer is posted, a paired payment is created
        with opposite payment_type and swapped journal_id & destination_journal_id.
        Both payments liquidity transfer lines are then reconciled.
        '''
        for payment in self:

            paired_payment = payment.copy({
                'journal_id': payment.destination_journal_id.id,
                'destination_journal_id': payment.journal_id.id,
                'payment_type': payment.payment_type == 'outbound' and 'inbound' or 'outbound',
                'move_id': None,
                'ref': payment.ref,
                'paired_internal_transfer_payment_id': payment.id,
                'date': payment.date,
            })
            paired_payment.move_id._post(soft=False)
            payment.paired_internal_transfer_payment_id = paired_payment

            body = _(
                "This payment has been created from %s",
                payment._get_html_link(),
            )
            paired_payment.message_post(body=body)
            body = _(
                "A second payment has been created: %s",
                paired_payment._get_html_link(),
            )
            payment.message_post(body=body)

            lines = (payment.move_id.line_ids + paired_payment.move_id.line_ids).filtered(
                lambda l: l.account_id == payment.destination_account_id and not l.reconciled)
            lines.reconcile()
            if payment.invoice_lines:
                payment.multipay()



class PaymentInvoiceLine(models.Model):
    _name = 'payment.invoice.line'
    
    check_line = fields.Boolean(
        string=' ',
    )
    payment_id = fields.Many2one('account.payment', string="Payment")
    invoice_id = fields.Many2one('account.move', string="Factura")
    invoice_line_id = fields.Many2one('account.move.line', compute='_get_invoice_data', string="line")
    invoice = fields.Char(related='invoice_id.name', string="Número de factura")
    #account_id = fields.Many2one(related="invoice_id.account_id", string="Account")
    date = fields.Date(string='Fecha de la factura', compute='_get_invoice_data', store=True)
    due_date = fields.Date(string='Fecha de vencimiento', compute='_get_invoice_data', store=True)
    total_amount = fields.Float(string='Total', compute='_get_invoice_data', store=True)
    open_amount = fields.Float(string='Monto adeudado', compute='_get_invoice_data', store=True)
    allocation = fields.Float(string='Monto pagado')
    account_move_line_id= fields.Many2one('account.move', string="Invoice")
    
    #@api.multi
    @api.depends(
        'invoice_id',
    )
    def _get_invoice_data(self):
        for data in self:
            invoice_id = data.invoice_id
            data.date = invoice_id.invoice_date
            data.due_date = invoice_id.invoice_date_due
            data.total_amount = invoice_id.amount_total 
            data.open_amount = invoice_id.amount_residual
            if invoice_id.move_type == 'out_invoice':
                # print("FACTURA CLIENTEEEEEEEEEEEEEEEEEEEEEEEE")
                data.invoice_line_id = self.env['account.move.line'].search([('debit', '!=', 0.0),('move_id','=', invoice_id.id)],limit=1).id
            elif invoice_id.move_type == 'in_invoice':
                # print("FACTURA PROVEEDORRRRRRRRRRRRRRRRRRRRRR")
                values = self.env['account.move.line'].search([('credit', '!=', 0.0),('move_id','=', invoice_id.id)])
                id_payable = self.env.ref('account.data_account_type_payable').id
                invoice_line = False
                if values:
                    for v in values:
                        if v.account_id.user_type_id.id == id_payable:
                            invoice_line = v.id

                data.invoice_line_id = invoice_line

class AccountMove(models.Model):
    _inherit = 'account.move'

    def js_assign_outstanding_lines(self,lines):
        if type(lines) == list:
            lines = self.env['account.move.line'].browse(lines)
        return lines.reconcile()
    
    
    pago = fields.Boolean(
        string='Pagar',
        
    )
    

class AccountMoveLines(models.Model):
    _inherit = 'account.move.line'

    invoice_id = fields.Many2one('account.move', string="Invoice")

