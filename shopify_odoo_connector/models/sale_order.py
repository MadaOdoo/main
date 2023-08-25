# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################

from odoo import models, fields
import logging
import requests
import json

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    shopify_instances_id = fields.Many2one('shopify.configuration',
                                           string="Shopify Instance")
    shopify_sync_ids = fields.One2many('shopify.sync', 'order_id')
    shopify_order_id = fields.Char('Shopify Order Id')
    shopify_instance_id = fields.Many2one('shopify.configuration',
                                          string="Shopify Instance")
    domain_bool = fields.Boolean()

    def sync_shopify_order(self):
        api_key = self.shopify_instances_id.con_endpoint
        password = self.shopify_instances_id.consumer_key
        store_name = self.shopify_instances_id.shop_name
        version = self.shopify_instances_id.version
        order_url = "https://%s:%s@%s/admin/api/%s/draft_orders.json" % (
            api_key, password, store_name, version)
        instance_ids = self.shopify_sync_ids.mapped('instance_id.id')
        if self.shopify_instance_id.id not in instance_ids:
            line_items = []
            for line in self.order_line:
                line_vals = {
                    "title": line.product_id.name,
                    "price": line.price_unit,
                    "quantity": int(line.product_uom_qty),
                }
                line_items.append(line_vals)
            payload = json.dumps({
                "draft_order": {
                    "line_items": line_items,
                    "email": self.partner_id.email,
                    "use_customer_default_address": True
                }
            })
            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.request("POST", order_url, headers=headers,
                                        data=payload)
            response_rec = response.json()
            response_order_id = response_rec['draft_order']['id']
            response_status = response_rec['draft_order']['status']
            response_name = response_rec['draft_order']['name']
            self.shopify_sync_ids.sudo().create({
                'instance_id': self.shopify_instances_id.id,
                'shopify_order_id': response_order_id,
                'shopify_order_name': response_name,
                'shopify_order_number': response_order_id,
                'order_status': response_status,
                'order_id': self.id,
                'synced_order': True,
            })
            self.shopify_order_id = response_order_id

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        api_key = self.shopify_instances_id.con_endpoint
        password = self.shopify_instances_id.consumer_key
        store_name = self.shopify_instances_id.shop_name
        version = self.shopify_instances_id.version
        if self.shopify_order_id and self.shopify_instances_id:
            order_complete_url = "https://%s:%s@%s/admin/api/%s/draft_orders/%s/complete.json" % (
                api_key, password, store_name, version, self.shopify_order_id)
            headers = {
                'Content-Type': 'application/json'
            }
            line_items = []
            for line in self.order_line:
                line_vals = {
                    "title": line.product_id.name,
                    "price": line.price_unit,
                    "quantity": int(line.product_uom_qty),

                }
                line_items.append(line_vals)
            payload = json.dumps({
                "draft_order": {
                    "line_items": line_items,
                    "email": self.partner_id.email,
                    "id": self.shopify_order_id,
                    "status": "completed",
                    "use_customer_default_address": True
                }
            })
            response = requests.request("PUT", order_complete_url,
                                        headers=headers,
                                        data=payload)

        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_refund_line = fields.Boolean('Is Refund Line', default=False,
                                    readonly=True)
    shopify_line_id = fields.Char('Shopify Line Id', readonly=True, store=True)
    shopify_instance_id = fields.Char('Shopify Instance Id', readonly=True)
    shopify_taxable = fields.Boolean('Line Item Taxable', default=False)
    shopify_tax_amount = fields.Float('Shopify Tax Amount')
    shopify_discount_amount = fields.Float('Shopify Discount Amount')
    shopify_line_item_discount = fields.Float('Line Item Discount')
    shopify_discount_code = fields.Char('Shopify Discount Code')
