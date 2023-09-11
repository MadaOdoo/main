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
import requests
from odoo import fields, models


class Collection(models.Model):
    """ Class for shopify collection.
        
        Methods:
            collection_update(self):
                Function to update shopify collection.
            _product_count(self):
                Function to get product count.
            collection_products(self):
                Method to show collection product in a window.
    """
    _name = 'collection'
    _description = 'Product Collection'

    name = fields.Char(required=True, help='Name for collection')
    shopify_instance_id = fields.Many2one('shopify.configuration',
                                          string="Shopify Instance",
                                          help='Id of shopify instance')
    collection_id = fields.Char(required=True, help='Id of collection')
    active = fields.Boolean(default=True,
                            help='Field to know if collection active or not')
    collect_product_count = fields.Integer(compute='_product_count',
                                           help='Count of product in collection')

    def collection_update(self):
        """Function to update shopify collection."""
        api_key = self.shopify_instance_id.con_endpoint
        password = self.shopify_instance_id.consumer_key
        store_name = self.shopify_instance_id.shop_name
        version = self.shopify_instance_id.version
        collection_id = self.collection_id
        return_url = "https://%s:%s@%s/admin/api/%s/collection/%s/products.json" % (
            api_key, password, store_name, version, collection_id)
        payload = []
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("GET", return_url,
                                    headers=headers, data=payload)
        data = response.json()
        products = data.get('products')
        for rec in products:
            product = self.env['product.template'].search(
                ['&', ('shopify_sync_ids.shopify_product_id', '=', rec['id']),
                 ('shopify_sync_ids.instance_id', '=',
                  self.shopify_instance_id.id)])

            if product:
                if self.id not in product.collection_ids.ids:
                    product.collection_ids = [(4, self.id)]

    def _product_count(self):
        """Function to get product count."""
        count = self.env['product.template'].search_count(
            ['&', ('collection_ids', '=', self.id), (
                'shopify_sync_ids.instance_id', '=', self.shopify_instance_id.id)])
        self.collect_product_count = count

    def collection_products(self):
        """ Method to show collection product in a window.

            dictionary: returns dictionary of window action.
        """
        return {
            'name': 'Collection Products',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'tree,form',
            'domain': [('collection_ids', '=', self.id)],
            'context': dict(self._context, create=False)
        }
