# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
import json
import requests
from odoo import fields, models


class SaleOrder(models.Model):
    """Class for inherited model sale.order

        Methods:
            def sync_shopify_order(self):
                Method to sync odoo orders into shopify.
            action_confirm(self):
                Supering the action_confirm function inorder to confirm the
                created sale order.
    """
    _inherit = 'sale.order'

    shopify_instance_id = fields.Many2one('shopify.configuration',
                                          string="Shopify Instance",
                                          help='Shopify instance id of sale order.')
    shopify_sync_ids = fields.One2many('shopify.sync', 'order_id',
                                       help='Shopify sync id of sale order.')
    shopify_order_id = fields.Char('Shopify Order Id',
                                   help='Shopify id of order')
    domain_bool = fields.Boolean()

    def sync_shopify_order(self):
        """Method to sync odoo orders into shopify"""
        api_key = self.shopify_instance_id.con_endpoint
        password = self.shopify_instance_id.consumer_key
        store_name = self.shopify_instance_id.shop_name
        version = self.shopify_instance_id.version
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
            if response_rec.get('draft_order'):
                response_order_id = response_rec['draft_order']['id']
                response_status = response_rec['draft_order']['status']
                response_name = response_rec['draft_order']['name']
                self.shopify_sync_ids.sudo().create({
                    'instance_id': self.shopify_instance_id.id,
                    'shopify_order_id': response_order_id,
                    'shopify_order_name': response_name,
                    'shopify_order_number': response_order_id,
                    'order_status': response_status,
                    'order_id': self.id,
                    'synced_order': True,
                })
                self.shopify_order_id = response_order_id

    def action_confirm(self):
        """Supering the action_confirm function inorder to confirm the created
           sale order.

           boolean: returns true or false
        """
        res = super(SaleOrder, self).action_confirm()
        api_key = self.shopify_instance_id.con_endpoint
        password = self.shopify_instance_id.consumer_key
        store_name = self.shopify_instance_id.shop_name
        version = self.shopify_instance_id.version
        if self.shopify_order_id and self.shopify_instance_id:
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
    """Class for inherited model sale.order.line"""
    _inherit = 'sale.order.line'

    is_refund_line = fields.Boolean('Is Refund Line', default=False,
                                    readonly=True,
                                    help='Will be true if the order line is a refund line')
    shopify_line_id = fields.Char('Shopify Line Id', readonly=True, store=True,
                                  help='Line id in shopify')
    shopify_instance_id = fields.Char('Shopify Instance Id', readonly=True,
                                      help='Shopify instance id')
    shopify_taxable = fields.Boolean('Line Item Taxable', default=False,
                                     help='Line item is taxable in shopify.')
    shopify_tax_amount = fields.Float('Shopify Tax Amount',
                                      help='Tax amount in shopify')
    shopify_discount_amount = fields.Float('Shopify Discount Amount',
                                           help='Discount amount in shopify')
    shopify_line_item_discount = fields.Float('Line Item Discount',
                                              help='Discount of line item in shopify.')
    shopify_discount_code = fields.Char('Shopify Discount Code',
                                        help='Discount code in shopify.')
