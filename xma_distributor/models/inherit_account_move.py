# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import http
from odoo.http import request, Response
from datetime import date, datetime

import requests

import logging

_logger = logging.getLogger(__name__)

class InheritAccountMove(models.Model):
    _inherit = 'account.move'

    pos_order_ids = fields.Many2many(
        "pos.order",
        string="Ordenes POS"
    )

    folio_vale = fields.Char(string="Folio del vale")

    distribuidora_id = fields.Many2one(
        "res.partner",
        string="Distribuidora"
    )
    
    sent = fields.Boolean(default=False)
    
    @api.model
    def _search_global_invoice(self):
        invoices = self.env['account.move'].sudo().search(['&', ('move_type', '=', 'out_invoice'), ('is_global_invoice', '!=', False), ('sent', '=', False)], limit=1)
        print(invoices)
        data = []
        for rec in invoices:
            folios = []
            for order in invoices.pos_order_ids:
                folios.append(order.folio_vale)
            
            if False in folios:
                folios.remove(False)
            
            print(folios)
            data.append({
                'folioFactura': rec.name,
                'creditos': folios
            })
        self.send_global_invoices(data)
    
    
    def send_global_invoices(self, data):

        # ACCESS TO SERVER
        #user = 'grupoedessacli'
        #password = 'Z#EHg50%NgI8'
        url = 'https://api-dev.prestavale.mx/api/creditosAfiliado/facturacion-mada'
        token_id = self.env['pos.config'].search([('token', '!=', False )], limit=1)
        print(token_id)
        print(token_id.token)
        params = {
            'access_token': token_id.token,
        }
        print("PARAMSS ", params)
        print(data)
        for rec in data:
            print(rec)
            response = requests.post(url, data=rec, params=params)
        
            if response.status_code == 400:
                error = response.content
                print('ERROR: ', error)
                print('Respuestaaa: ', response)
                print('CODIGO:', response.status_code)
                print('JSON: ', response.text)
                print('URL ', response.url)
                _logger.warning(
                "#################NO-ENVIADO#################\n")
            elif response.status_code == 200:
                print(response.status_code)
                _logger.warning(
                "#################ENVIADO#################\n")
                for fac in data:
                    invoice = self.env['account.move'].sudo().search([('name', '=', fac.get('folioFactura'))], limit=1)
                    invoice.sudo().write({'sent': True})
            else:
                error = response.content
                print('ERROR: ', error)
                print('Respuestaaa: ', response)
                print('CODIGO:', response.status_code)
                print('JSON: ', response.text)
                print('URL ', response.url)
                _logger.warning(
                "#################NO-ENVIADO#################\n")
