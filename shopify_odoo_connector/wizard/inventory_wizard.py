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
import re
import requests
from odoo import fields, models


class InventoryWizard(models.TransientModel):
    """Class for transient model inventory.wizard.

        Methods:
            sync_inventory(self):
                method to sync inventory from shopify to odoo.
    """
    _name = 'inventory.wizard'
    _description = 'Inventory Wizard'

    import_inventory = fields.Selection(string='Import/Export',
                                        selection=[('shopify', 'To Shopify'),
                                                   ('odoo', 'From Shopify')],
                                        required=True, default='odoo',
                                        help='Field to choose type of data exchange')
    shopify_instance_id = fields.Many2one('shopify.configuration',
                                          string="Shopify Instance",
                                          required=True,
                                          help='Id of shopify instance')

    def sync_inventory(self):
        """method to sync inventory from shopify to odoo"""
        shopify_instance = self.shopify_instance_id
        api_key = self.shopify_instance_id.con_endpoint
        password = self.shopify_instance_id.consumer_key
        store_name = self.shopify_instance_id.shop_name
        version = self.shopify_instance_id.version
        warehouse = shopify_instance.warehouse_id
        if self.import_inventory == 'shopify':
            inventory_url = "https://%s:%s@%s/admin/api/%s/inventory_items.json" % (
                api_key, password, store_name, version)
        else:
            inventory_url = "https://%s:%s@%s/admin/api/%s/products.json" % (
                api_key, password, store_name, version)
            payload = []
            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.request("GET", inventory_url,
                                        headers=headers,
                                        data=payload)
            j = response.json()
            inventory = j['products']
            inventory_link = response.headers[
                'link'] if 'link' in response.headers else ''
            inventory_links = inventory_link.split(',')
            for link in inventory_links:
                match = re.compile(r'rel=\"next\"').search(link)
                if match:
                    inventory_link = link
            rel = re.search('rel=\"(.*)\"', inventory_link).group(
                1) if 'link' in response.headers else ''
            if inventory_link and rel == 'next':
                i = 0
                n = 1
                while i < n:
                    page_info = re.search('page_info=(.*)>',
                                          inventory_link).group(1)
                    limit = re.search('limit=(.*)&', inventory_link).group(1)
                    inventory_link = "https://%s:%s@%s/admin/api/%s/products.json?limit=%s&page_info=%s" % (
                        api_key, password, store_name, version, limit,
                        page_info)
                    response = requests.request('GET', inventory_link,
                                                headers=headers, data=payload)
                    j = response.json()
                    new_inventory = j['products']
                    inventory += new_inventory
                    inventory_link = response.headers['link']
                    inventory_links = inventory_link.split(',')
                    for link in inventory_links:
                        match = re.compile(r'rel=\"next\"').search(link)
                        if match:
                            inventory_link = link
                    rel = re.search('rel=\"next\"', inventory_link)
                    i += 1
                    if inventory_link and rel is not None:
                        n += 1
            for inv in inventory:
                try:
                    if inv['options']:
                        for variant in inv['variants']:
                            product = self.env['product.product'].sudo().search(
                                [('shopify_sync_ids.shopify_product_id', '=', variant['id']),
                                 ('shopify_sync_ids.instance_id', '=', shopify_instance.id),
                                 ('detailed_type', '=', 'product'),
                                 ('company_id', '=',
                                  shopify_instance.company_id.id)])
                            if product:
                                exist_inventory = self.env[
                                    'stock.quant'].sudo().search(
                                    [(
                                        'location_id', '=',
                                        warehouse.lot_stock_id.id),
                                        ('product_id', '=', product.id),
                                        ('lot_id', '=', False),
                                        ('company_id', '=',
                                         shopify_instance.company_id.id)]
                                )
                                if exist_inventory:
                                    exist_inventory.sudo().action_set_inventory_quantity()
                                    exist_inventory.inventory_quantity = \
                                        exist_inventory.inventory_quantity + variant['inventory_quantity']
                                    exist_inventory.sudo().action_apply_inventory()
                                else:
                                    inventory_update = {
                                        'product_id': product.id,
                                        'inventory_quantity': variant[
                                            'inventory_quantity'],
                                        'location_id': warehouse.lot_stock_id.id
                                    }
                                    self.env['stock.quant'].with_context(
                                        inventory_mode=True).create(
                                        inventory_update).action_apply_inventory()
                    else:
                        product = self.env['product.product'].sudo().search(
                            [('shopify_sync_ids.shopify_product_id', '=', inv['id']),
                             ('shopify_sync_ids.instance_id', '=', shopify_instance.id),
                             ('detailed_type', '=', 'product'),
                             ('company_id', '=', shopify_instance.company_id.id)])
                        if product:
                            exist_inventory = self.env['stock.quant'].sudo().search(
                                [('location_id', '=', warehouse.lot_stock_id.id),
                                 ('product_id', '=', product.id),
                                 ('lot_id', '=', False),
                                 ('company_id', '=', shopify_instance.company_id.id)]
                            )
                            if exist_inventory:
                                exist_inventory.sudo().action_set_inventory_quantity()
                                exist_inventory.inventory_quantity = exist_inventory.inventory_quantity + \
                                                                     inv['inventory_quantity']
                                exist_inventory.sudo().action_apply_inventory()
                            else:
                                inventory_update = {
                                    'product_id': product.id,
                                    'inventory_quantity': inv['inventory_quantity'],
                                    'location_id': warehouse.lot_stock_id.id
                                }
                                self.env['stock.quant'].with_context(
                                    inventory_mode=True).create(
                                    inventory_update).action_apply_inventory()
                except Exception as e:
                    self.env['log.message'].sudo().create({
                        'name': 'Inventory Syncing not processed for id : ' + str(inv['id']),
                        'shopify_instance_id': shopify_instance.id,
                        'model': 'Stock Quantity',
                    })
