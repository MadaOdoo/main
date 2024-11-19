# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import http
from odoo.http import request, Response
from datetime import date, datetime
import json
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
    apply_voucher = fields.Boolean(related="company_id.apply_voucher")
    
    @api.model
    def _search_global_invoice(self):
        invoices = self.env['account.move'].sudo().search(['&', ('move_type', '=', 'out_invoice'), ('is_global_invoice', '!=', False), ('sent', '=', False)], limit=1)
        data = []
        for rec in invoices:
            folios = []
            for order in invoices.pos_order_ids:
                folios.append(order.folio_vale)
            if False in folios:
                folios.remove(False)
            data.append({
                'folioFactura': rec.name,
                'creditos': folios
            })
        self.send_global_invoices(data)
    
    
    def send_global_invoices(self, data):
        
        token_id = self.env['res.config.settings'].search([('token', '!=', False )], limit=1)
        url = 'https://api-dev.prestavale.mx/api/creditosAfiliado/facturacion-mada/'
        params = {
            'access_token': token_id.token,
        }
        headers = {
            'Content-Type': 'application/json',
        }
        
        for rec in data:
            response = requests.post(url, params=params, headers=headers, data=json.dumps(rec))
        
            if response.status_code == 400:
                error = response.content
                _logger.warning(
                "#################NO-ENVIADO#################\n")
                _logger.warning(error)
            elif response.status_code == 200:
                _logger.warning(
                "#################ENVIADO#################\n")
                _logger.warning(str(rec))
                for fac in data:
                    invoice = self.env['account.move'].sudo().search([('name', '=', fac.get('folioFactura'))], limit=1)
                    invoice.sudo().write({'sent': True})
            else:
                error = response.content
                _logger.warning(
                "#################NO-ENVIADO#################\n")
                _logger.warning(error)