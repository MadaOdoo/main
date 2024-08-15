# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from collections import defaultdict
from odoo.exceptions import UserError, AccessError
from odoo.tools import float_is_zero, float_compare
from datetime import datetime
import logging
import pprint
from datetime import date

class InheritPosSession(models.Model):
    _inherit = 'pos.session'
    
    
    def get_order_pos_session(self, session):
        orders = self.env['pos.order'].search([('session_id', '=', session.id)])
        print('===============================')
        print(orders)
        return orders
    
    def new_list_orders(self, lista):
        nueva_lista = []
        #monto = 0
        order = []
        folio = ""
        #totales_dict = {'total_vale': 0, 'total_otros': 0}
        total_p = 0
        total_o = 0
        print('//////////////\n')
        print('NEWLISTORDERS')
        totales_dict = {}
        for rec in lista:
            payment = self.env['pos.payment'].search([('pos_order_id', '=', rec.id)])
            print(payment)
            
            if rec.folio_vale:
                folio += rec.folio_vale + ", " 
            order.append([4, rec.id, 0])
            
            
            for pay in payment:
                print('payyyyyyyyyyy', pay)
                print('payyyyyyyyyyy', pay.payment_method_id.id)
                print('payyyyyyyyyyy', pay.payment_method_id.name)
                
                if pay.payment_method_id.name in totales_dict:
                    totales_dict[pay.payment_method_id.name][0] += pay.amount
                else:
                    totales_dict[pay.payment_method_id.name] = [pay.amount, pay.payment_method_id.journal_id, pay.payment_method_id.id]
                
                
                # if pay.payment_method_id.id == 6:
                #     total_p += pay.amount
                # else:
                #     total_o += pay.amount
            
            #totales_dict['total_vale'] = total_p
            #totales_dict['total_otros'] = total_o
            
            print('TOTALESS_DICT: ', totales_dict)
                
                
            #precio = ((rec.pos_order_id.pago_quincenal) * (rec.pos_order_id.cantidad_pagos) * (float(rec.pos_order_id.porcentaje_comision) / 100)) / 1.16
            #monto += precio
            
        nueva_lista.append({
            #'monto': monto, 
            'order_ids': order,
            'folio': folio,
            'totales': totales_dict
        })
        print('/////////////////////finnewlistordre\n\n')
        return nueva_lista
    
    # def get_payment_method(self, payment):
    #     sessions = self.env['pos.payment'].search([('session_id', '=', payment.id)])
    #     domain = [("session_id", "=", payment.id)]
    #     payment_method_data = self.env['pos.payment'].read_group(domain, ['ids_pay:array_agg(id)', 'ids_dis:array_agg(distribuidora_id)', 'ids_order:array_agg(pos_order_id)', 'amount'], ['payment_method_id'])
    #     print("**********************************GETPAYMENTMETHOD**")
    #     print(payment_method_data)
    #     set_payment_method = set(session['payment_method_id'][0] for session in payment_method_data)
    #     print(set_payment_method)
    
    #     return set_payment_method
    
    # def create_list_payment(self, method, payments):
    #     list_payment = []
    #     for pay in payments:
    #         if pay.payment_method_id == method:
    #         list_payment.append(pay)
    #     return list_payment
    
    # def crear_lista_metodos_pagos(self, method, payment):
    #     #domain = ['&', ("session_id", "=", payment.id), ('payment_method_id', '=', method)]
    #     domain = [("session_id", "=", payment.id)]
    #     payment_order = self.env['pos.payment'].search(domain)
    #     print("************************************")
    #     print(payment_order)
    #     return payment_order
    
    # def totales_lista_metodos_pagos(self, method, payment):
    #     domain = ['&', ("session_id", "=", payment.id), ('payment_method_id', '=', method)]
    #     domain = [("session_id", "=", payment.id)]
    #     payment_order = self.env['pos.payment'].search(domain)
    #     print("************************************")
    #     print(payment_order)
    #     return payment_order

    # def crear_nueva_lista(self, lista):
    #     nueva_lista = []
    #     monto = 0
    #     order = []
    #     folio = ""
    #     for rec in lista:
    #         precio = ((rec.pos_order_id.pago_quincenal) * (rec.pos_order_id.cantidad_pagos) * (float(rec.pos_order_id.porcentaje_comision) / 100)) / 1.16
    #         monto += precio
    #         if rec.pos_order_id.folio_vale:
    #             folio += rec.pos_order_id.folio_vale + ", " 
    #         order.append([4, rec.pos_order_id.id, 0])
    #     nueva_lista.append({
    #         'distribuidora': rec.pos_order_id.distribuidora_id.id, 
    #         'monto': monto, 
    #         'order_ids': order,
    #         'folio': folio,
    #         'method': rec.payment_method_id.id
    #     })
    #     return nueva_lista
    
    # def lista_monto_por_metodos(self, order, method):
    #     monto_pay = self.env['pos.payment'].search([('pos_order_id', '=', order.id), ('payment_method_id', '=', method)], limit=1)
    #     print('kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk')
    #     print(monto_pay)
    #     print(monto_pay.amount)
    #     if rec['method'] == 6:
    
   
    
    def create_manual_global_invoice(self, records):
       
        for pos_session in records:

            pos_journal, global_customer = self._check_session_can_be_invoiced(pos_session)
            global_journal = pos_session.config_id.global_journal_id
            orders = self.get_order_pos_session(pos_session)
            print("***********ORDENESS\n")
            print(orders)
            print("****************NUEVAAAA****\n\n")
            nueva = self.new_list_orders(orders)
            print(nueva)

            for rec in nueva:
                print("///////", rec)
                print(rec['totales'])
                total_div = rec['totales']
  
                if total_div.get('Prestavale'):
                    prestavale = total_div['Prestavale']
                    print('PRESTAVAELEEE ', prestavale)
                    monto_prestavale = prestavale[0]
                    print(monto_prestavale)
                
                account_move = self.env['account.move'].with_context(default_journal_id=pos_journal.id).create({
                    'journal_id': pos_journal.id,
                    'date': fields.Date.context_today(self),
                    'ref': '',
                })
                print('---create_manual_global_invoice---account_move:', account_move)
                
                global_invoice = self.env['account.move'].with_context(default_journal_id=global_journal.id).create({
                    'company_id': 1,
                    'journal_id': global_journal.id,
                    'date': fields.Date.context_today(self),
                    #'invoice_date': fields.Date.context_today(self),
                    #'invoice_date_due':,
                    'l10n_mx_edi_payment_method_id': 22,
                    #'l10n_mx_edi_payment_policy': 'PDD',
                    'invoice_payment_term_id': 21,
                    'l10n_mx_edi_usage': 'S01',
                    'ref': '',
                    'partner_id': 928,
                    'pos_order_ids': rec['order_ids'],
                    'folio_vale': rec['folio'],
                    #'distribuidora_id': rec['distribuidora'],
                    'move_type': 'out_invoice',
                    'is_global_invoice': True,
                    'periodicidad': pos_session.config_id.global_periodicity
                })
            
                print('---create_manual_global_invoice---global_invoice:', global_invoice)
            
                print('--------create_manual_global_invoice--------pos_session:', pos_session)
                self._set_references_global_invoice(pos_session, account_move, global_invoice)
                datos = self.create_values_in_data(account_move, global_invoice, pos_session, None)
                print('---------------create_manual_global_invoice----------------datos:', datos)

                invoice_lines_no_negatives = []
                print('---------create_values_in_data------------session y order:', pos_session, rec)
                
                for line in datos.get('invoice_lines'):
                    print('---------create_values_in_data---------line---session y order:', pos_session, rec)
                  
                    print('----create_values_in_data--line if:', line)
                    if line['product_id'] in map(lambda n: n['product_id'], invoice_lines_no_negatives):
                        line_to_modify = next(x for x in invoice_lines_no_negatives if line['product_id'] == x['product_id'])
                        invoice_lines_no_negatives[invoice_lines_no_negatives.index(line_to_modify)]['quantity'] += line['quantity']
                    else:
                        invoice_lines_no_negatives.append(line)
                        print('----create_values_in_data----else-invoice_lines_no_negatives:', invoice_lines_no_negatives)
                print('----create_values_in_data---global_invoice:', list(global_invoice))
                global_invoice.write({
                    'invoice_line_ids': [(0, None, invoice_line) for invoice_line in
                                         invoice_lines_no_negatives],
                })
                
                if global_invoice.line_ids:
                    print('---------------create_manual_global_invoice---------global_invoice.lines_ids:', list(global_invoice.line_ids))
                    global_invoice._post()
                    if global_invoice.line_ids and global_invoice.state == 'posted':
                        move_lines = self.env['account.move.line'].search([
                            ('move_id', 'in', (global_invoice.id, account_move.id)),
                            ('account_id', '=', pos_session.config_id.global_customer_id.property_account_receivable_id.id),
                            ('name', '!=', 'From invoiced orders'),
                            ('reconciled', '=', False)
                        ])
                        move_lines.reconcile()
                    
                        
                    print('LINESSSIDSS  ', global_invoice.line_ids)
                
                if total_div.get('Prestavale'):
                    lineas = []
                    credit = {
                        "account_id": 3,
                        "credit": monto_prestavale,
                        "move_id": global_invoice.id
                    }
                    debit = {
                        "account_id": 20062,#20062,
                        "debit": monto_prestavale,
                        "move_id": global_invoice.id
                    }
                    lineas.append([0, 0, credit])
                    lineas.append([0, 0, debit])
                    print(lineas)
                    
                    asiento_prestavale = self.env['account.move'].create({
                        'company_id': 1,
                        'journal_id': prestavale[1].id,
                        'date': fields.Date.context_today(self),
                        'ref': global_invoice.name,
                        'pos_order_ids': rec['order_ids'],
                        'folio_vale': rec['folio'],
                        'move_type': 'entry',
                        'tax_cash_basis_origin_move_id': global_invoice.id,
                        'line_ids': lineas
                    }).action_post()
                
                #global_invoice.with_context(check_move_validity=False, skip_invoice_sync=True).update({'line_ids': lineas})
                
                #global_invoice._search_global_invoice()
                #global_invoice.write({
                #    'sent': True,
                #})
                
                for pago in total_div:
                    print("//////////////////////////////////////////* ", total_div[pago][1])
                    if not total_div[pago][2] == 6:
                        pay_register = self.env['account.payment.register']\
                           .with_context(active_model='account.move', active_ids=global_invoice.ids)\
                               .create({
                                   'company_id': 1,
                                   'amount': total_div[pago][0],
                                   'payment_date': '2024-05-16',
                                   'journal_id': total_div[pago][1].id,
                                   'partner_id': 928,
                                   'pos_order_ids': rec['order_ids']})._create_payments()
                        
                        pay_register.write({
                            'journal_id': total_div[pago][1],
                            'partner_id': 928,
                            'amount': total_div[pago][0],
                            'pos_order_ids': rec['order_ids'],
                            'payment_method_line_id': 1
                        })
                               
                        print(pay_register)
                               
                monto_total = 0
                product_record = self.env.ref("xma_distributor.product_billing_service")
                for vale in global_invoice.pos_order_ids:
                    monto = 0
                    print('valeeeeee', vale)
                    if vale.is_vale:
                        monto = ((vale.pago_quincenal) * (vale.cantidad_pagos) * (float(vale.porcentaje_comision) / 100)) / 1.16
                        print(monto)
                    monto_total += monto
                    print(monto_total)
                    vals_nota = {
                        'product_id': product_record.id,
                        'quantity': 1,
                        'product_uom_id': 1,
                        'price_unit': monto_total,
                    }
                        
                nota_credito = self.env['account.move'].create({
                    'company_id': 1,
                    'journal_id': 100,
                    'invoice_date': fields.Date.context_today(self),
                    'l10n_mx_edi_payment_method_id': 22,
                    'l10n_mx_edi_payment_policy': 'PPD',
                    'l10n_mx_edi_usage': 'S01',
                    'ref': '',
                    'partner_id': 928,
                    #'distribuidora_id': vale.distribuidora_id.id,
                    'move_type': 'out_refund',
                    'pos_order_ids': global_invoice.pos_order_ids,
                    'folio_vale': rec['folio'],
                    'is_global_invoice': False,
                    'periodicidad': pos_session.config_id.global_periodicity,
                    'invoice_line_ids': [(0, None, vals_nota)]
                })
                        
                        # if not vale.str_fechas_pagare:
                        #     print("El valor fecha es Falso")
                            #     fechas = None
                            # elif vale.str_fechas_pagare == "":
                                #     print("El valor fecha esta vacío")
                                #     fechas = None
                                # else:
                                #     fechas = vale.str_fechas_pagare.split(",")
                                
                                # for num in range(1, vale.cantidad_pagos + 1):
                                #     print('nummm', num)
                                #     date_pay = None
                                #     if fechas:
                                #         if len(fechas) >= num:
                                #             date_pay =  datetime.strptime(fechas[num - 1], '%d/%m/%Y').date()
                                #         else:
                                #             date_pay = None
                                    
                                #     line_invoice = {'invoice_id': global_invoice.id}
                                #     valores = {
                                #         'journal_id': 100,
                                #         'date': date_pay,
                                #         'ref': str(num) + " " + vale.folio_vale,
                                #         'partner_id': 928,
                                #         'distribuidora_id': vale.distribuidora_id.id,
                                #         'amount': float(vale.pago_quincenal),
                                #         'pos_order_ids': vale,
                                #         'folio_vale': vale.folio_vale,
                                #         'payment_method_line_id': 1
                                #     }
                                #     print('ANTES DE CREATE PAYMENT')
                                #     pago = self.env['account.payment'].create(valores)
                                #     print('DESPUES DE CREATE PAYMENT Y ANTES DE WRITE')
                                #     pago.write({
                                #         'invoice_lines': [(0, None, line_invoice)],
                                #         'state': 'posted'
                                #     })
                                #     print('DESPUES DE WRITE PAYMENT')
    
                            # pagos_sumados = {}
                            # for pay in vale.payment_ids:
                            #     tipo_pago = pay.payment_method_id.id
                            #     amot= pay.amount
                            #     print(tipo_pago)
                            #     print(amot)
                            #     if tipo_pago != 100:
                            #         if tipo_pago in pagos_sumados:
                            #             pagos_sumados[tipo_pago] += amot
                            #         else:
                            #             pagos_sumados[tipo_pago] = amot
                            # print(pagos_sumados, "********************************")
    
    
            
            for order in pos_session.order_ids:
                order.write({'to_invoice': True})
        
        records.write({'has_global_invoice': True})
    

    def create_values_in_data(self, account_move, global_invoice, pos_session, bank_payment_method_diffs):
        print('----------------------------------create_values_in_data-------------------------------------')
        data = {'bank_payment_method_diffs': bank_payment_method_diffs or {}}
        data = pos_session._accumulate_amounts_global_invoice(data)
        #print('---data1111111', data)
        data = pos_session._create_non_reconciliable_move_lines(data)
        #print('---data2222222', data)
        data = pos_session._create_bank_payment_moves(data)
        #print('---data3333333', data)
        data = pos_session._create_cash_statement_lines_and_cash_move_lines(data)
        #print('---data4444444', data)
        data = pos_session._create_invoice_receivable_lines(data)
        #print('---data5555555', data)
        data = pos_session._create_stock_output_lines(data)
        #print('---data6666666', data)
        data = pos_session._create_balancing_line(data, balancing_account=False, amount_to_balance=0)
        #print('---data7777777', data)

        # if account_move.line_ids:
        #     clina_pos = pos_session.company_id.account_default_pos_receivable_account_id.id
        #     clina = pos_session.config_id.global_customer_id.property_account_receivable_id.id
        #     amount_without_refunds = sum([(order.amount_total if not order.to_invoice and order.amount_total > 0 else 0.0) for order in pos_session.order_ids])
        #     refunds = sum([(order.amount_total if not order.to_invoice and order.amount_total < 0 else 0.0) for order in pos_session.order_ids])
        #     amount_total = amount_without_refunds + refunds
            
        #     accounting_lines = [

        #         {'move_id': account_move.id, 'account_id': clina_pos, 'name': 'Por VENTAS-REEMBOLSOS de POS',
        #          'debit': amount_total, 'check_global_invoice': True, 'partner_id': pos_session.config_id.global_customer_id.id},
        #         {'move_id': account_move.id, 'account_id': clina, 'name': 'Por VENTAS-REEMBOLSOS de POS',
        #          'credit': amount_total, 'check_global_invoice': True, 'partner_id': pos_session.config_id.global_customer_id.id},
        #     ]
          
        #     lines = accounting_lines
        #     pos_session.env['account.move.line'].sudo().with_company(self.company_id).with_context(check_move_validity=False).create(lines)

        #     currlines = self.env['account.move.line'].search([('move_id', '=', account_move.id)])
            
           
        #     pos_session.env['account.move.line'].search([(
        #         'move_id', '=', account_move.id),
        #         ('check_global_invoice', '=', False)]).unlink()  # TODO Aca se rompe el picking
        #     account_move._post()
            
        # try:
        #     data = pos_session.sudo().with_company(self.company_id)._reconcile_account_move_lines(data)
        #     data = pos_session.with_company(self.company_id)._reconcile_account_move_lines_stock(data)
        # except:
        #     pass

        invoice_lines_no_negatives = []
        #for order in pos_session.order_ids:
            #print('---------create_values_in_data------------session y order:', pos_session, order)
        
        for line in data.get('invoice_lines'):
            #print('---------create_values_in_data---------line---session y order:', pos_session, order)
            #print('---------create_values_in_data--------distri_line y distri_order:', line['distribuidora_id'], int(order.distribuidora_id))
            #if line['distribuidora_id'] == int(order.distribuidora_id):
            #    print('----create_values_in_data--line if:', line)
                if line['product_id'] in map(lambda n: n['product_id'], invoice_lines_no_negatives):
                    line_to_modify = next(x for x in invoice_lines_no_negatives if line['product_id'] == x['product_id'])
                    invoice_lines_no_negatives[invoice_lines_no_negatives.index(line_to_modify)]['quantity'] += line['quantity']
                else:
                    invoice_lines_no_negatives.append(line)
                    #print('----create_values_in_data----else-invoice_lines_no_negatives:', invoice_lines_no_negatives)
        #print('----create_values_in_data---global_invoice:', list(global_invoice))
        # global_invoice.write({
        #     'invoice_line_ids': [(0, None, invoice_line) for invoice_line in
        #                          invoice_lines_no_negatives],
        # })
        #print('----create_values_in_data---global_invoice_invoice_line_ids:', global_invoice.invoice_line_ids)
        return data
                    
                
    
    def _accumulate_amounts_global_invoice(self, data):
        print('----------------------------------_accumulate_amounts_global_invoice-------------------------------------')
        amounts = lambda: {'amount': 0.0, 'amount_converted': 0.0}
        tax_amounts = lambda: {'amount': 0.0, 'amount_converted': 0.0, 'base_amount': 0.0, 'base_amount_converted': 0.0}
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
        combine_inv_payment_receivable_lines = defaultdict(lambda: self.env['account.move.line'])
        split_inv_payment_receivable_lines = defaultdict(lambda: self.env['account.move.line'])
        rounded_globally = self.company_id.tax_calculation_rounding_method == 'round_globally'
        pos_receivable_account = self.company_id.account_default_pos_receivable_account_id
        currency_rounding = self.currency_id.rounding
        invoice_lines = []
        total_paid_orders = 0
        for order in self.order_ids: 
            print('------_accumulate_amounts_global_invoice----------order:', order)
            print('---------_accumulate_amounts_global_invoice-----------Distribuidora:', order.distribuidora_id.name)
            order_is_invoiced = order.is_invoiced
            for payment in order.payment_ids:
                print('-----_accumulate_amounts_global_invoice---------payment:', payment)
                amount = payment.amount
                if float_is_zero(amount, precision_rounding=currency_rounding):
                    continue
                date = payment.payment_date
                payment_method = payment.payment_method_id
                is_split_payment = payment.payment_method_id.split_transactions
                payment_type = payment_method.type

                if payment_type != 'pay_later':
                    if is_split_payment and payment_type == 'cash':
                        split_receivables_cash[payment] = self._update_amounts(split_receivables_cash[payment],
                                                                               {'amount': amount}, date)
                    elif not is_split_payment and payment_type == 'cash':
                        combine_receivables_cash[payment_method] = self._update_amounts(
                            combine_receivables_cash[payment_method], {'amount': amount}, date)
                    elif is_split_payment and payment_type == 'bank':
                        split_receivables_bank[payment] = self._update_amounts(split_receivables_bank[payment],
                                                                               {'amount': amount}, date)
                    elif not is_split_payment and payment_type == 'bank':
                        combine_receivables_bank[payment_method] = self._update_amounts(
                            combine_receivables_bank[payment_method], {'amount': amount}, date)

                    if order_is_invoiced:
                        print('-------_accumulate_amounts_global_invoice-------order_is_invoiced:')
                        if is_split_payment:
                            split_inv_payment_receivable_lines[payment] |= payment.account_move_id.line_ids.filtered(lambda line: line.account_id == pos_receivable_account)
                            split_invoice_receivables[payment] = self._update_amounts(split_invoice_receivables[payment], {'amount': payment.amount}, order.date_order)
                        else:
                            combine_inv_payment_receivable_lines[payment_method] |= payment.account_move_id.line_ids.filtered(lambda line: line.account_id == pos_receivable_account)
                            combine_invoice_receivables[payment_method] = self._update_amounts(combine_invoice_receivables[payment_method], {'amount': payment.amount}, order.date_order)
                    else:
                        print('-------_accumulate_amounts_global_invoice-----order_is_invoiced else')

                if payment_type == 'pay_later' and not order_is_invoiced:
                    if is_split_payment:
                        split_receivables_pay_later[payment] = self._update_amounts(
                            split_receivables_pay_later[payment], {'amount': amount}, date)
                    elif not is_split_payment:
                        combine_receivables_pay_later[payment_method] = self._update_amounts(
                            combine_receivables_pay_later[payment_method], {'amount': amount}, date)

            if not order_is_invoiced:
                print('-------_accumulate_amounts_global_invoice------not order_is_invoiced:')
                # Create global invoice lines
                for order_line in order.lines:
                    print('----------_accumulate_amounts_global_invoice------------order_line:', order_line)
                    print('qty', order_line.qty)
                    invoice_line = order._prepare_global_invoice_line(order_line)
                    fiscal_position = self.move_id.fiscal_position_id
                    accounts = order_line.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
                    name = 'Ticket: ' + order.pos_reference + ' | ' + invoice_line.get('name'),
                    distri = order.distribuidora_id

                    invoice_line.update({
                        'move_id': self.move_id.id,
                        # 'exclude_from_invoice_tab': False,
                        'display_type': 'product',
                        'account_id': accounts['income'].id,
                        'name': name,
                        'price_subtotal': order_line.price_subtotal_incl,
                        'quantity': order_line.qty,
                        'product_id': order_line.product_id.id,
                        'distribuidora_id': distri.id,
                    })
                    invoice_lines.append(invoice_line)
                    total_paid_orders = order_line.price_subtotal_incl
                order.partner_id._increase_rank('customer_rank')

        if self.company_id.anglo_saxon_accounting:
            global_session_pickings = self.picking_ids.filtered(lambda p: not p.pos_order_id)
            if global_session_pickings:
                stock_moves = self.env['stock.move'].sudo().search([ # TODO: Mostrar
                    ('picking_id', 'in', global_session_pickings.ids),
                    ('company_id.anglo_saxon_accounting', '=', True),
                    ('product_id.categ_id.property_valuation', '=', 'real_time'),
                ])
                for move in stock_moves:
                    exp_key = move.product_id._get_product_accounts()['expense']
                    out_key = move.product_id.categ_id.property_stock_account_output_categ_id
                    amount = -sum(move.stock_valuation_layer_ids.mapped('value'))
                    stock_expense[exp_key] = self._update_amounts(stock_expense[exp_key], {'amount': amount},
                                                                  move.picking_id.date, force_company_currency=True)
                    if move.location_id.usage == 'customer':
                        stock_return[out_key] = self._update_amounts(stock_return[out_key], {'amount': amount},
                                                                     move.picking_id.date, force_company_currency=True)
                    else:
                        stock_output[out_key] = self._update_amounts(stock_output[out_key], {'amount': amount},
                                                                     move.picking_id.date, force_company_currency=True)
        MoveLine = self.env['account.move.line'].with_context(check_move_validity=False, skip_invoice_sync=True)
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
            'combine_inv_payment_receivable_lines': combine_inv_payment_receivable_lines,
            'rounding_difference': rounding_difference,
            'MoveLine': MoveLine,
            'invoice_lines': invoice_lines,
            'total_paid_orders': total_paid_orders,
            'split_invoice_receivables': split_invoice_receivables,
            'split_inv_payment_receivable_lines': split_inv_payment_receivable_lines,
        })
        return data
    
    def cron_create_global_invoice(self):
        registros = self.env["pos.session"].search([("has_global_invoice", "=", False)])
        self.create_manual_global_invoice(registros)
    
    
    # def create_manual_global_invoice(self, records):
       
    #     for pos_session in records:

    #         pos_journal, global_customer = self._check_session_can_be_invoiced(pos_session)
    #         global_journal = pos_session.config_id.global_journal_id
    #         pay_method = self.get_payment_method(pos_session)
    #         print("***********METODODEPAGO\n")
    #         print(pay_method)
    #         print("********************\n\n")
            
    #         lista_def = []
    #         for pay in pay_method:
    #             print(pay)
    #             dist = self.get_distribuidoras(pay, pos_session)
    #             print("***********DISTRIBUIDORAS\n")
    #             print(dist)
    #             print("********************\n\n")
    #             for dis in dist:
    #                 print(dis)
    #                 lista_def = self.crear_lista_distribuidoras(pay, dis, pos_session)
    #                 print(lista_def)
    #                 nueva = self.crear_nueva_lista(lista_def)
    #                 print("nueva\n",nueva)
    #                 for rec in nueva:
    #                     print("///////", rec)
    #                     account_move = self.env['account.move'].with_context(default_journal_id=pos_journal.id).create({
    #                         'journal_id': pos_journal.id,
    #                         'date': fields.Date.context_today(self),
    #                         'ref': '',
    #                     })
    #                     print('---create_manual_global_invoice---account_move:', account_move)
            
    #                     global_invoice = self.env['account.move'].with_context(default_journal_id=global_journal.id).create({
    #                         'journal_id': global_journal.id,
    #                         'date': fields.Date.context_today(self),
    #                         'l10n_mx_edi_payment_method_id': rec['method'] if rec['method'] == 1 else 22,
    #                         'ref': '',
    #                         'partner_id': 928,
    #                         'pos_order_ids': rec['order_ids'],
    #                         'folio_vale': rec['folio'],
    #                         'distribuidora_id': rec['distribuidora'],
    #                         'move_type': 'out_invoice',
    #                         'is_global_invoice': True,
    #                         'periodicidad': pos_session.config_id.global_periodicity,
    #                         'l10n_mx_edi_payment_policy': 'PPD' if rec['method'] == 6 else 'PUE'
    #                     })
    #                     print('---create_manual_global_invoice---global_invoice:', global_invoice)
                    
    #                     print('--------create_manual_global_invoice--------pos_session:', pos_session)
    #                     self._set_references_global_invoice(pos_session, account_move, global_invoice)
    #                     datos = self.create_values_in_data(account_move, global_invoice, pos_session, None)
    #                     print('---------------create_manual_global_invoice----------------datos:', datos)
        
    #                     invoice_lines_no_negatives = []
    #                     print('---------create_values_in_data------------session y order:', pos_session, rec)
                        
    #                     for line in datos.get('invoice_lines'):
    #                         print('---------create_values_in_data---------line---session y order:', pos_session, rec)
    #                         print('---------create_values_in_data--------distri_line y distri_order:', line['distribuidora_id'], int(rec['distribuidora']))
    #                         if line['distribuidora_id'] == int(rec['distribuidora']):
    #                             print('----create_values_in_data--line if:', line)
    #                             if line['product_id'] in map(lambda n: n['product_id'], invoice_lines_no_negatives):
    #                                 line_to_modify = next(x for x in invoice_lines_no_negatives if line['product_id'] == x['product_id'])
    #                                 invoice_lines_no_negatives[invoice_lines_no_negatives.index(line_to_modify)]['quantity'] += line['quantity']
    #                             else:
    #                                 invoice_lines_no_negatives.append(line)
    #                                 print('----create_values_in_data----else-invoice_lines_no_negatives:', invoice_lines_no_negatives)
    #                     print('----create_values_in_data---global_invoice:', list(global_invoice))
    #                     global_invoice.write({
    #                         'invoice_line_ids': [(0, None, invoice_line) for invoice_line in
    #                                              invoice_lines_no_negatives],
    #                     })
        
    #                     if global_invoice.line_ids:
    #                         print('---------------create_manual_global_invoice---------global_invoice.lines_ids:', list(global_invoice.line_ids))
    #                         global_invoice._post()
    #                         if global_invoice.line_ids and global_invoice.state == 'posted':
    #                             move_lines = self.env['account.move.line'].search([
    #                                 ('move_id', 'in', (global_invoice.id, account_move.id)),
    #                                 ('account_id', '=', pos_session.config_id.global_customer_id.property_account_receivable_id.id),
    #                                 ('name', '!=', 'From invoiced orders'),
    #                                 ('reconciled', '=', False)
    #                             ])
    #                             move_lines.reconcile()
                        
                       
    #                     monto = 0
    #                     por = self.env["ir.config_parameter"].get_param("xma_distributor.percentage")
    #                     product_record = self.env.ref("xma_distributor.product_billing_service")
    #                     for vale in global_invoice.pos_order_ids:
    #                         print('valeeeeee', vale)
    #                         if vale.is_vale:
    #                             monto = ((vale.pago_quincenal) * (vale.cantidad_pagos) * (float(vale.porcentaje_comision) / 100)) / 1.16
    #                             vals_nota = {
    #                                 'product_id': product_record.id,
    #                                 'quantity': 1,
    #                                 'product_uom_id': 1,
    #                                 'price_unit': monto,
    #                             }
    #                             nota_credito = self.env['account.move'].with_context(default_journal_id=global_journal.id).create({
    #                                 'journal_id': global_journal.id,
    #                                 'invoice_date': fields.Date.context_today(self),
    #                                 'ref': '',
    #                                 'partner_id': 928,
    #                                 'distribuidora_id': vale.distribuidora_id.id,
    #                                 'move_type': 'out_refund',
    #                                 'pos_order_ids': vale,
    #                                 'folio_vale': vale.folio_vale,
    #                                 'is_global_invoice': False,
    #                                 'periodicidad': pos_session.config_id.global_periodicity,
    #                                 'invoice_line_ids': [(0, None, vals_nota)]
    #                             })
    
    #                             if not vale.str_fechas_pagare:
    #                                 print("El valor fecha es Falso")
    #                                 fechas = None
    #                             elif vale.str_fechas_pagare == "":
    #                                 print("El valor fecha esta vacío")
    #                                 fechas = None
    #                             else:
    #                                 fechas = vale.str_fechas_pagare.split(",")
                                
    #                             for num in range(1, vale.cantidad_pagos + 1):
    #                                 print('nummm', num)
    #                                 date_pay = None
    #                                 if fechas:
    #                                     if len(fechas) >= num:
    #                                         date_pay =  datetime.strptime(fechas[num - 1], '%d/%m/%Y').date()
    #                                     else:
    #                                         date_pay = None
                                    
    #                                 line_invoice = {'invoice_id': global_invoice.id}
    #                                 valores = {
    #                                     'journal_id': 100,
    #                                     'date': date_pay,
    #                                     'ref': str(num) + " " + vale.folio_vale,
    #                                     'partner_id': 928,
    #                                     'distribuidora_id': vale.distribuidora_id.id,
    #                                     'amount': float(vale.pago_quincenal),
    #                                     'pos_order_ids': vale,
    #                                     'folio_vale': vale.folio_vale,
    #                                     'payment_method_line_id': 1
    #                                 }
    #                                 print('ANTES DE CREATE PAYMENT')
    #                                 pago = self.env['account.payment'].create(valores)
    #                                 print('DESPUES DE CREATE PAYMENT Y ANTES DE WRITE')
    #                                 pago.write({
    #                                     'invoice_lines': [(0, None, line_invoice)],
    #                                     'state': 'posted'
    #                                 })
    #                                 print('DESPUES DE WRITE PAYMENT')
    
    #                         pagos_sumados = {}
    #                         for pay in vale.payment_ids:
    #                             tipo_pago = pay.payment_method_id.id
    #                             amot= pay.amount
    #                             print(tipo_pago)
    #                             print(amot)
    #                             if tipo_pago != 100:
    #                                 if tipo_pago in pagos_sumados:
    #                                     pagos_sumados[tipo_pago] += amot
    #                                 else:
    #                                     pagos_sumados[tipo_pago] = amot
    #                         print(pagos_sumados, "********************************")
    
    #                         for res, mon in pagos_sumados.items():
    #                             print(res)
    #                             metodo_pago = self.env["pos.payment.method"].browse(res)
    #                             print(metodo_pago)
    #                             print(metodo_pago.name)
    #                             res_invoice = {'invoice_id': global_invoice.id}
    #                             val = {
    #                                 'journal_id': metodo_pago.journal_id.id,
    #                                 'date': date_pay,
    #                                 'ref': " P" ,
    #                                 'partner_id': 928,
    #                                 'distribuidora_id': vale.distribuidora_id.id,
    #                                 'amount': float(mon),
    #                                 'pos_order_ids': vale,
    #                             }
    #                             pago_res = self.env['account.payment'].create(val)
    #                             pago_res.write({
    #                                 'invoice_lines': [(0, None, res_invoice)],
    #                                 'state': 'posted'
    #                             })
    
            
    #         for order in pos_session.order_ids:
    #             order.write({'to_invoice': True})
        
    #     records.write({'has_global_invoice': True})

    # def create_manual_global_invoice(self, records):
       
    #     for pos_session in records:

    #         pos_journal, global_customer = self._check_session_can_be_invoiced(pos_session)
    #         global_journal = pos_session.config_id.global_journal_id
    #         distribuidoras = self.get_distribuidoras(pos_session.order_ids)
    #         print("***********DISTRIBUIDORAS\n")
    #         print(distribuidoras)
    #         print("********************\n\n")
            
    #         lista_def = []
    #         for distri in distribuidoras:
    #             lista_def = self.crear_lista_distribuidoras(distri, pos_session.order_ids)
    #             print(lista_def)
    #             nueva = self.crear_nueva_lista(lista_def)
    #             print("nueva\n",nueva)
    #             for rec in nueva:
    #                 print("///////", rec)
    #                 account_move = self.env['account.move'].with_context(default_journal_id=pos_journal.id).create({
    #                     'journal_id': pos_journal.id,
    #                     'date': fields.Date.context_today(self),
    #                     'ref': '',
    #                 })
    #                 print('---create_manual_global_invoice---account_move:', account_move)
        
    #                 global_invoice = self.env['account.move'].with_context(default_journal_id=global_journal.id).create({
    #                     'journal_id': global_journal.id,
    #                     'date': fields.Date.context_today(self),
    #                     'ref': '',
    #                     'partner_id': 928,
    #                     'pos_order_ids': rec['order_ids'],
    #                     'folio_vale': rec['folio'],
    #                     'distribuidora_id': rec['distribuidora'],
    #                     'move_type': 'out_invoice',
    #                     'is_global_invoice': True,
    #                     'periodicidad': pos_session.config_id.global_periodicity,
    #                 })
    #                 print('---create_manual_global_invoice---global_invoice:', global_invoice)
                
    #                 print('--------create_manual_global_invoice--------pos_session:', pos_session)
    #                 self._set_references_global_invoice(pos_session, account_move, global_invoice)
    #                 datos = self.create_values_in_data(account_move, global_invoice, pos_session, None)
    #                 print('---------------create_manual_global_invoice----------------datos:', datos)
    
    #                 invoice_lines_no_negatives = []
    #                 print('---------create_values_in_data------------session y order:', pos_session, rec)
                    
    #                 for line in datos.get('invoice_lines'):
    #                     print('---------create_values_in_data---------line---session y order:', pos_session, rec)
    #                     print('---------create_values_in_data--------distri_line y distri_order:', line['distribuidora_id'], int(rec['distribuidora']))
    #                     if line['distribuidora_id'] == int(rec['distribuidora']):
    #                         print('----create_values_in_data--line if:', line)
    #                         if line['product_id'] in map(lambda n: n['product_id'], invoice_lines_no_negatives):
    #                             line_to_modify = next(x for x in invoice_lines_no_negatives if line['product_id'] == x['product_id'])
    #                             invoice_lines_no_negatives[invoice_lines_no_negatives.index(line_to_modify)]['quantity'] += line['quantity']
    #                         else:
    #                             invoice_lines_no_negatives.append(line)
    #                             print('----create_values_in_data----else-invoice_lines_no_negatives:', invoice_lines_no_negatives)
    #                 print('----create_values_in_data---global_invoice:', list(global_invoice))
    #                 global_invoice.write({
    #                     'invoice_line_ids': [(0, None, invoice_line) for invoice_line in
    #                                          invoice_lines_no_negatives],
    #                 })
    
    #                 if global_invoice.line_ids:
    #                     print('---------------create_manual_global_invoice---------global_invoice.lines_ids:', list(global_invoice.line_ids))
    #                     global_invoice._post()
    #                     if global_invoice.line_ids and global_invoice.state == 'posted':
    #                         move_lines = self.env['account.move.line'].search([
    #                             ('move_id', 'in', (global_invoice.id, account_move.id)),
    #                             ('account_id', '=', pos_session.config_id.global_customer_id.property_account_receivable_id.id),
    #                             ('name', '!=', 'From invoiced orders'),
    #                             ('reconciled', '=', False)
    #                         ])
    #                         move_lines.reconcile()
                    
                   
    #                 monto = 0
    #                 por = self.env["ir.config_parameter"].get_param("xma_distributor.percentage")
    #                 product_record = self.env.ref("xma_distributor.product_billing_service")
    #                 for vale in global_invoice.pos_order_ids:
    #                     print('valeeeeee', vale)
    #                     if vale.is_vale:
    #                         monto = ((vale.pago_quincenal) * (vale.cantidad_pagos) * (float(por) / 100)) / 1.16
    #                         vals_nota = {
    #                             'product_id': product_record.id,
    #                             'quantity': 1,
    #                             'product_uom_id': ,
    #                             'price_unit': monto,
    #                         }
    #                         nota_credito = self.env['account.move'].with_context(default_journal_id=global_journal.id).create({
    #                             'journal_id': global_journal.id,
    #                             'invoice_date': fields.Date.context_today(self),
    #                             'ref': '',
    #                             'partner_id': 928,
    #                             'distribuidora_id': vale.distribuidora_id.id,
    #                             'move_type': 'out_refund',
    #                             'pos_order_ids': vale,
    #                             'folio_vale': vale.folio_vale,
    #                             'is_global_invoice': False,
    #                             'periodicidad': pos_session.config_id.global_periodicity,
    #                             'invoice_line_ids': [(0, None, vals_nota)]
    #                         })

    #                         if not vale.str_fechas_pagare:
    #                             print("El valor fecha es Falso")
    #                             fechas = None
    #                         elif vale.str_fechas_pagare == "":
    #                             print("El valor fecha esta vacío")
    #                             fechas = None
    #                         else:
    #                             fechas = vale.str_fechas_pagare.split(",")
                            
    #                         for num in range(1, vale.cantidad_pagos + 1):
    #                             print('nummm', num)
    #                             date_pay = None
    #                             if fechas:
    #                                 if len(fechas) >= num:
    #                                     date_pay =  datetime.strptime(fechas[num - 1], '%d/%m/%Y').date()
    #                                 else:
    #                                     date_pay = None
                                
    #                             line_invoice = {'invoice_id': global_invoice.id}
    #                             valores = {
    #                                 'journal_id': 100,
    #                                 'date': date_pay,
    #                                 'ref': str(num) + " " + vale.folio_vale,
    #                                 'partner_id': 928,
    #                                 'distribuidora_id': vale.distribuidora_id.id,
    #                                 'amount': float(vale.pago_quincenal),
    #                                 'pos_order_ids': vale,
    #                                 'folio_vale': vale.folio_vale,
    #                                 'payment_method_line_id': 1
    #                             }
    #                             print('ANTES DE CREATE PAYMENT')
    #                             pago = self.env['account.payment'].create(valores)
    #                             print('DESPUES DE CREATE PAYMENT Y ANTES DE WRITE')
    #                             pago.write({
    #                                 'invoice_lines': [(0, None, line_invoice)],
    #                                 'state': 'posted'
    #                             })
    #                             print('DESPUES DE WRITE PAYMENT')

    #                     pagos_sumados = {}
    #                     for pay in vale.payment_ids:
    #                         tipo_pago = pay.payment_method_id.id
    #                         amot= pay.amount
    #                         print(tipo_pago)
    #                         print(amot)
    #                         if tipo_pago != 100:
    #                             if tipo_pago in pagos_sumados:
    #                                 pagos_sumados[tipo_pago] += amot
    #                             else:
    #                                 pagos_sumados[tipo_pago] = amot
    #                     print(pagos_sumados, "********************************")

    #                     for res, mon in pagos_sumados.items():
    #                         print(res)
    #                         metodo_pago = self.env["pos.payment.method"].browse(res)
    #                         print(metodo_pago)
    #                         print(metodo_pago.name)
    #                         res_invoice = {'invoice_id': global_invoice.id}
    #                         val = {
    #                             'journal_id': metodo_pago.journal_id.id,
    #                             'date': date_pay,
    #                             'ref': " P" ,
    #                             'partner_id': 928,
    #                             'distribuidora_id': vale.distribuidora_id.id,
    #                             'amount': float(mon),
    #                             'pos_order_ids': vale,
    #                         }
    #                         pago_res = self.env['account.payment'].create(val)
    #                         pago_res.write({
    #                             'invoice_lines': [(0, None, res_invoice)],
    #                             'state': 'posted'
    #                         })

        
    #         for order in pos_session.order_ids:
    #             order.write({'to_invoice': True})
        
    #     records.write({'has_global_invoice': True})

        # return {
        #     'name': _('Global invoice'),
        #     'view_mode': 'form',
        #     'res_model': 'account.move',
        #     'type': 'ir.actions.act_window',
        #     'res_id': global_invoice.id,
        # }
