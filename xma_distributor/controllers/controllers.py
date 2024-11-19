
import json
import copy
import traceback
import datetime

from odoo import http
from odoo.http import request, Response
from datetime import date, datetime

import requests

import logging


_logger = logging.getLogger(__name__)


class EndpointsConnection(http.Controller):
    
    unauthorized = {
        "ok": False,
        "msg": "Does not have authorization",
        "data": ""
    }
    
    @staticmethod
    def _validate_user(access):
        """ User Validation """
        try:
            user_admin = request.env["res.users"].sudo().search(
                [("login", "=", access.get("user")), 
                 ("password_api", "=", access.get("password"))], limit=1)
            if user_admin:
                return True
        except:
            return False
           
            
    @staticmethod
    def _create_payment(vals):
        data = vals.get("pagos")
        if data:
            for rec in data:
                invoice = request.env['account.move'].sudo().search([('name', '=', rec.get('folioFactura'))], limit=1)
                pay_register = request.env['account.payment.register']\
                    .sudo().with_context(active_model='account.move', active_ids=invoice.ids)\
                    .create({
                            'journal_id': 118, #id de branch xmarts 05/08/2024 link: https://www.odoo.sh/project/madamx/branches/xmarts/history
                            'partner_id': 928,
                            'amount': rec.get('monto')
                        
                        })._create_payments()
                line_invoice = {'invoice_id': invoice.id}
                pay_register.sudo().write({
                    'state': 'posted',
                    'folio_vale': rec.get('folioVale'),
                    'payment_number_per_folio': rec.get('folioNumPago'),
                    'voucher_payment_date' : rec.get('folioFecha'),
                    'l10n_mx_edi_payment_method_id': 3
                })
        return {"ok": True, "data": data, "msg": "Recibido exitosamente."}
        
    @http.route('/api/prestavale/', auth='public', type='json', methods=['POST'], csrf_token=False)
    def get_prestavales(self, **kw):
        try:
            access = self._validate_user(json.loads(request.httprequest.data))
            if not access:
                return self.unauthorized
            return self._create_payment(json.loads(request.httprequest.data))
        except:
            return self._create_payment(json.loads(request.httprequest.data))
