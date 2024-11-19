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
        orders = self.env['pos.order'].search([
            ('session_id', '=', session.id),
            ('account_move', '=', False)
        ])
        return orders
    
    def new_list_orders(self, order_ids):
        nueva_lista = []
        folio = ""
        for rec in order_ids:
            if rec.folio_vale:
                folio += rec.folio_vale + ", "
        nueva_lista.append({
            'order_ids': order_ids.ids,
            'folio': folio,
            'totales': self.dict_payments_data(order_ids)
        })
        return nueva_lista

    def create_manual_global_invoice(self, records):
        super(InheritPosSession, self).create_manual_global_invoice(records)
        for pos_session in records:
            nueva = pos_session.new_list_orders(pos_session.order_ids.filtered(lambda x: not x.account_move))
            global_invoice = pos_session.global_invoice_id
            for rec in nueva:
                global_invoice.write({"folio_vale": rec['folio']})
                global_invoice.write({"pos_order_ids": rec['order_ids']})
                total_div = rec['totales']
                if total_div.get('Prestavale'):
                    prestavale = total_div['Prestavale']
                    monto_prestavale = prestavale[0]
                if total_div.get('Prestavale'):
                    lineas = []
                    credit = {
                        "account_id": 4,
                        "credit": monto_prestavale,
                    }
                    debit = {
                        "account_id": 20062,
                        "debit": monto_prestavale,
                    }
                    lineas.append([0, 0, credit])
                    lineas.append([0, 0, debit])
                    self.env['account.move'].create({
                        'company_id': 1,
                        'journal_id': prestavale[1].id,
                        'date': fields.Date.context_today(self),
                        #'ref': global_invoice.name,
                        'pos_order_ids': rec['order_ids'],
                        'folio_vale': rec['folio'],
                        'move_type': 'entry',
                        #'tax_cash_basis_origin_move_id': global_invoice.id,
                        'line_ids': lineas
                    }).action_post()
                               
                monto_total = 0
                product_record = self.env.ref("xma_distributor.product_billing_service")
                for vale in pos_session.order_ids.filtered(lambda x: not x.account_move):
                    monto = 0
                    if vale.is_vale:
                        monto = ((vale.pago_quincenal) * (vale.cantidad_pagos) * (float(vale.porcentaje_comision) / 100)) / 1.16
                    monto_total += monto
                    vals_nota = {
                        'product_id': product_record.id,
                        'quantity': 1,
                        'product_uom_id': 1,
                        'price_unit': monto_total,
                    }
                nota_credito = self.env['account.move'].create({
                    'company_id': 1,
                    'journal_id': 100,
                    'l10n_mx_edi_payment_method_id': 22,
                    'l10n_mx_edi_payment_policy': 'PPD',
                    'l10n_mx_edi_usage': 'S01',
                    'partner_id': 928,
                    'move_type': 'out_refund',
                    'pos_order_ids': pos_session.order_ids.filtered(lambda x: not x.account_move),
                    'folio_vale': rec['folio'],
                    'is_global_invoice': False,
                    'periodicidad': pos_session.config_id.global_periodicity,
                    'invoice_line_ids': [(0, None, vals_nota)]
                })
                nota_credito.action_post()
                move_line = self.env['account.move.line'].search([
                        ('move_id', 'in', (pos_session.global_invoice_id.id, nota_credito.id)),
                        ('account_id', '=', 3),
                        ('reconciled', '=', False)
                ])
                move_line.reconcile()
                pos_session.global_invoice_payment_move_id.line_ids.filtered(lambda x: "Prestavale" in x.name).remove_move_reconcile
            for order in pos_session.order_ids:
                order.write({'to_invoice': True})
        records.write({'has_global_invoice': True})
    
    def cron_create_global_invoice(self):
        registros = self.env["pos.session"].search([("has_global_invoice", "=", False)])
        # self.create_manual_global_invoice(registros)
