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


class ResPartners(models.Model):
    """Class for inherited model res.partner
        Methods:
            sync_shopify_customer(self):
                Method to sync odoo partners into shopify.
    """
    _inherit = 'res.partner'

    shopify_instance_id = fields.Many2one('shopify.configuration',
                                          string="Shopify Instance",
                                          help='Shopify instance id of partner')
    synced_customer = fields.Boolean(readonly=True, store=True,
                                     help='Will be true for synced customer.')
    shopify_customer_id = fields.Char('Shopify Id', readonly=True,
                                      help='Partner id in shopify')
    shopify_sync_ids = fields.One2many('shopify.sync', 'customer_id',
                                       help='shopify sync id')

    def sync_shopify_customer(self):
        """Method to sync odoo partners into shopify."""
        api_key = self.shopify_instance_id.con_endpoint
        password = self.shopify_instance_id.consumer_key
        store_name = self.shopify_instance_id.shop_name
        version = self.shopify_instance_id.version
        customer_url = "https://%s:%s@%s/admin/api/%s/customers.json" % (
            api_key, password, store_name, version)
        instance_ids = self.shopify_sync_ids.mapped('instance_id.id')
        if self.shopify_instance_id.id not in instance_ids:
            payload = json.dumps({
                "customer": {
                    "first_name": self.name,
                    "last_name": "",
                    "email": self.email or '',
                    "verified_email": True,
                    "addresses": [
                        {
                            "address1": self.street,
                            "city": self.city,
                            "province": self.state_id.name or "",
                            "zip": self.zip,
                            "last_name": "",
                            "first_name": self.name,
                            "country": self.country_id.name or ''
                        }
                    ],
                    "send_email_invite": True
                }
            })
            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.request("POST", customer_url, headers=headers,
                                        data=payload)
            response_rec = response.json()
            if response_rec.get('customer'):
                response_customer_id = response_rec['customer']['id']
                self.shopify_sync_ids.sudo().create({
                    'instance_id': self.shopify_instance_id.id,
                    'shopify_customer_id': response_customer_id,
                    'customer_id': self.id,
                })
