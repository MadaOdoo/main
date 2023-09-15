# -*- coding: utf-8 -*-
# File:           madkting_config.py
# Author:         Gerardo Lopez
# Copyright:      (C) 2019 All rights reserved by Madkting
# Created:        2023-04-18

import requests

from odoo import models, fields, api
from odoo import exceptions
from datetime import datetime
from ..log.logger import logger
from ..responses import results

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_invoice_folio(self):
        company_id = self.env.user.company_id.id
        config = self.env['madkting.config'].get_config()
        doc_id = config.cafs_document_type_id.id
        domain = [
            ("state", "=", "posted"),
            ("company_id", "=", company_id), 
            ("l10n_latam_document_type_id", "=", doc_id),
        ]
        logger.info(f"Busca factura folio: {domain}")
        invoice = self.env['account.move'].search(domain, limit=1, order="id desc")
        if invoice:
            return invoice.name
        logger.info("No se obtuvieron resultados de la busqueda.")
        return

    @api.model
    def invoice_order(self, order_id):

        if not order_id:
            return results.error_result(code='order_id_required',
                                        description='order_id is required')
        order = self.search([('id', '=', order_id)])
        
        config = self.env['madkting.config'].get_config()

        if config and config.validate_cafs and config.cafs_document_type_id:
            
            company_id = self.env.user.company_id.id
            invoice_folio = self._get_invoice_folio()
            doc_id = config.cafs_document_type_id.id

            if not invoice_folio:
                err_msg = "No se pudo obtener el ultimo folio de las facturas"
                logger.error(err_msg)
                order.message_post(body=err_msg)
                return results.error_result(code='folio_not_found',
                                        description='order {} invoice folio not found'.format(order_id))

            invoice_separator = config.invoice_separator
            logger.info(f"Separador serie y folio {invoice_separator}")
            last_folio = invoice_folio.split(invoice_separator)
            logger.info(last_folio)
            last_folio = last_folio[1]
            logger.info(f"Folio: {last_folio}")

            new_folio = int(last_folio) + 1

            caf = self.env['l10n_cl.dte.caf'].sudo().search([
                ('final_nb', '>=', new_folio), ('start_nb', '<=', new_folio), ('l10n_latam_document_type_id', '=', doc_id),
                ('status', '=', 'in_use'), ('company_id', '=', company_id)], limit=1)

            if not caf:
                err_msg = "No se encontraron folios disponibles"
                logger.error(err_msg)
                order.message_post(body=err_msg)
                return results.error_result(code='folio_not_available',
                                        description='{} para facturar la orden {}'.format(err_msg, order_id))

            return super(SaleOrder, self).invoice_order(order_id)
        
        else:
            return super(SaleOrder, self).invoice_order(order_id)