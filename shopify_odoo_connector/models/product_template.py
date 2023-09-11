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


class ProductTemplate(models.Model):
    """Class for inherited model product.template.

        Methods:
            def sync_shopify_product(self):
                Method to export odoo product to shopify.
    """
    _inherit = 'product.template'

    shopify_instance_id = fields.Many2one('shopify.configuration',
                                          string="Shopify Instance",
                                          help='Shopify instance id of synced product.')
    synced_product = fields.Boolean(readonly=False, store=True,
                                    help='Will be true for the synced product.')
    shopify_product_id = fields.Char('Shopify Product Id', readonly=True,
                                     help='Shopify id product.')
    collection_ids = fields.Many2many('collection', string='Collections',
                                      readonly=True,
                                      help='Collection id of product')
    shopify_sync_ids = fields.One2many('shopify.sync', 'product_id',
                                       help='Shopify sync id of product.')
    gift_card = fields.Boolean(string='Gift Card', readonly=True,
                               help='will be true for the gift card product.')

    def sync_shopify_product(self):
        """Method to export odoo product to shopify."""
        api_key = self.shopify_instance_id.con_endpoint
        password = self.shopify_instance_id.consumer_key
        store_name = self.shopify_instance_id.shop_name
        version = self.shopify_instance_id.version
        product_url = "https://%s:%s@%s/admin/api/%s/products.json" % (
            api_key, password, store_name, version)
        instance_ids = self.shopify_sync_ids.mapped('instance_id.id')
        if self.shopify_instance_id.id not in instance_ids:
            variants = []
            for line in self.product_variant_ids:
                line_vals = {
                    "option1": line.partner_ref,
                    "price": line.lst_price,
                    "inventory_quantity": int(line.qty_available),
                    "barcode": line.barcode if line.barcode else None,
                    "sku": line.default_code if line.default_code else None,
                    "id": self.id,
                    "product_id": self.id,
                }
                variants.append(line_vals)
            if not variants:
                line_vals = {
                    "id": self.id,
                    "product_id": self.id,
                    "title": self.name,
                    "body_html": self.description_sale
                    if self.description_sale else '',
                    "price": self.list_price,
                    "inventory_quantity": int(self.qty_available),
                    "sku": self.default_code if self.default_code else None,
                    "unitCost": self.standard_price,
                    "product_type": 'Storable Product'
                    if self.type == 'product' else 'Consumable'
                    if self.type == 'consu' else 'Service',
                    "barcode": self.barcode if self.barcode else None,
                }
                variants.append(line_vals)
            payload = json.dumps({
                "product": {
                    'id': self.id,
                    "title": self.name,
                    "body_html": self.description_sale,
                    "price": self.list_price
                    if self.description_sale else "",
                    "inventory_quantity": int(self.qty_available),
                    "sku": self.default_code if self.default_code else None,
                    "barcode": self.barcode if self.barcode else None,
                    "product_type": 'Storable Product'
                    if self.type == 'product' else 'Consumable'
                    if self.type == 'consu' else 'Service',
                    "unitCost": self.standard_price,
                    "variants": variants,
                }
            })
            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.request("POST", product_url, headers=headers,
                                        data=payload)
            response_rec = response.json()
            if response_rec.get('product'):
                response_product_id = response_rec['product']['id']
                self.shopify_sync_ids.sudo().create({
                    'instance_id': self.shopify_instance_id.id,
                    'shopify_product_id': response_product_id,
                    'product_id': self.id,
                })
                for prod_variants, items in zip(self.product_variant_ids,
                                                response_rec['product'][
                                                    'variants']):
                    prod_variants.shopify_sync_ids.sudo().create({
                        'instance_id': self.shopify_instance_id.id,
                        'shopify_product_id': items['id'],
                        'product_prod_id': prod_variants.id,
                    })
