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


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    shopify_instance_id = fields.Many2one('shopify.configuration',
                                          string="Shopify Instance")
    synced_product = fields.Boolean(readonly=False, store=True)
    shopify_product_id = fields.Char('Shopify Product Id', readonly=True)
    collections_ids = fields.Many2many('collections', string='Collections',
                                       readonly=True)
    shopify_sync_ids = fields.One2many('shopify.sync', 'product_id')
    gift_card = fields.Boolean(string='Gift Card', readonly=True)

    def sync_shopify_product(self):
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
            response_product_id = response_rec['product']['id']
            self.shopify_sync_ids.sudo().create({
                'instance_id': self.shopify_instance_id.id,
                'shopify_product_id': response_product_id,
                'product_id': self.id,
            })
            for prod_variants, items in zip(self.product_variant_ids,response_rec['product']['variants']):
                prod_variants.shopify_sync_ids.sudo().create({
                    'instance_id': self.shopify_instance_id.id,
                    'shopify_product_id': items['id'],
                    'product_prod_id': prod_variants.id,
                })


class ProductProduct(models.Model):
    _inherit = 'product.product'

    shopify_variant_id = fields.Char('Shopify Variant Id', readonly=True)
    shopify_instance_id = fields.Many2one('shopify.configuration',
                                          'Shopify Instance')
    shopify_sync_ids = fields.One2many('shopify.sync', 'product_prod_id')

    def sync_shopify_product(self):
        api_key = self.shopify_instance_id.con_endpoint
        password = self.shopify_instance_id.consumer_key
        store_name = self.shopify_instance_id.shop_name
        version = self.shopify_instance_id.version

        product_url = "https://%s:%s@%s/admin/api/%s/products.json" % (
            api_key, password, store_name, version)
        instance_ids = self.shopify_sync_ids.mapped('instance_id.id')
        if self.shopify_instance_id.id not in instance_ids:
            variants = []
            for line in self.attribute_line_ids.value_ids:
                line_vals = {
                    "option1": line.name,
                    "price": self.list_price,
                    "sku": self.default_code if self.default_code else None,
                    'inventory_quantity': self.qty_available,
                    'barcode': self.barcode if self.barcode else None,
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
                    "sku": self.default_code if self.default_code else None,
                    "inventory_quantity": int(self.qty_available),
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
                    "body_html": self.description_sale
                    if self.description_sale else "",
                    "sku": self.default_code if self.default_code else None,
                    "barcode":self.barcode if self.barcode else None,
                    "inventory_quantity": int(self.qty_available),
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
            response = requests.request("POST", product_url,
                                        headers=headers, data=payload)
            response_rec = response.json()
            response_product_id = response_rec['product']['id']
            self.shopify_sync_ids.sudo().create({
                'instance_id': self.shopify_instance_id.id,
                'shopify_product_id': response_product_id,
                'product_prod_id': self.id,
            })


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    shopify_attribute_id = fields.Char('Shopify Product Id', readonly=True)
    shopify_instance_id = fields.Many2one('shopify.configuration',
                                          'Shopify Instance', readonly=True)
