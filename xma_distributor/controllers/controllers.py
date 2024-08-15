
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

    # error_500 = {
    #     "ok": False,
    #     "msg": "Ha ocurrido un error, reenviar nuevamente.",
    #     "data": ""
    # }
    
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
        print("DATAAAAAAAAA", data)
        if data:
            for rec in data:
                print("RECCCCC", rec)
                invoice = request.env['account.move'].sudo().search([('name', '=', rec.get('folioFactura'))], limit=1)
                pay_register = request.env['account.payment.register']\
                    .sudo().with_context(active_model='account.move', active_ids=invoice.ids)\
                    .create({
                            'journal_id': 118, #id de branch xmarts 05/08/2024 link: https://www.odoo.sh/project/madamx/branches/xmarts/history
                            #'ref': str(num) + " " + vale.folio_vale,
                            'partner_id': 928,
                            'amount': rec.get('monto'),
                            #'pos_order_ids': vale,
                            #'payment_method_line_id': 6
                        })._create_payments()
                line_invoice = {'invoice_id': invoice.id}
                pay_register.sudo().write({
                    'state': 'posted',
                    'folio_vale': rec.get('folioVale'),
                    'payment_number_per_folio': rec.get('folioNumPago'),
                    'voucher_payment_date' : rec.get('folioFecha'),
                })
                print(pay_register)
        return {"ok": True, "data": data, "msg": "Recibido exitosamente."}
        
    @http.route('/api/prestavale/', auth='public', type='json', method=['POST'], csrf_token=False)
    def get_prestavales(self, **kw):
        try:
            print(json.loads(request.httprequest.headers))
            access = self._validate_user(json.loads(request.httprequest.data))
            print(json.loads(request.httprequest.data))
            if not access:
                return self.unauthorized
            return self._create_payment(json.loads(request.httprequest.data))
        except:
            return self._create_payment(json.loads(request.httprequest.data))
        
        #token_id = request.env['pos.config'].sudo().search([('token', '!=', False )], limit=1)
        #print(token_id)
        #print(token_id.token)
        #token = 'access_token=' + token_id.token
        #print(token)
        #print(type(token))
        #print('hht: ', request.httprequest)
        #print('headers: ', request.httprequest.headers)
        #print('Params: ', request.httprequest.query_string)
        #print(request.httprequest.content_type)
        #params = request.httprequest.query_string
        #print('data: ', request.httprequest.data)
        #print(json.loads(request.httprequest.data))
        #print(params)
        #param = params.decode()
        #print(param)
        
        #if token == param:
        #    print('yeiii')
        #    return self._create_payment(json.loads(request.httprequest.data))