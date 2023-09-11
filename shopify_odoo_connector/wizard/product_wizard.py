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
import base64
import json
import logging
import pprint
import re
import requests
from odoo import models, fields
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ProductWizard(models.TransientModel):
    """ class for transient model product wizard.

        Methods:
            sync_products(self):
                method to create queue jobs for exporting and importing data.
            import_products_from_shopify(self, shopify_products):
                method to import products from shopify to odoo.Queue job
                evokes this method for creating products in odoo.
            export_products_to_shopify(self, product):
                method to export products from odoo to shopify.Queue job
                evokes this method to export odoo products.
            create_product_by_id(self,shopify_instance, api_key, password,
                store_name, version, product): method to create a specific
                shopify product to odoo by product id.
    """
    _name = 'product.wizard'
    _description = 'Product Wizard'

    import_products = fields.Selection(string='Import/Export',
                                       selection=[('shopify', 'To Shopify'),
                                                  ('odoo', 'From Shopify')],
                                       required=True, default='odoo',
                                       help='selection field to choose data exchange type.')
    shopify_instance_id = fields.Many2one('shopify.configuration',
                                          string="Shopify Instance",
                                          required=True,
                                          help='Id of shopify instance')
    import_inventory = fields.Boolean('Import Inventory', default=False,
                                      help='Will import inventory of product if true.')

    def sync_products(self):
        """method to create queue jobs for exporting and importing data."""
        if self.import_products == 'shopify' and not self.shopify_instance_id.import_product:
            raise ValidationError(
                'For Syncing Products to Shopify Enable Export product option in shopify configuration ')
        else:
            api_key = self.shopify_instance_id.con_endpoint
            password = self.shopify_instance_id.consumer_key
            store_name = self.shopify_instance_id.shop_name
            version = self.shopify_instance_id.version
            if self.import_products == 'shopify':
                products = self.env['product.template'].search([])
                product_list = []
                size = 50
                for i in range(0, len(products), size):
                    product_list.append(products[i:i + size])
                for product in product_list:
                    delay = self.with_delay(priority=1, eta=60)
                    delay.export_products_to_shopify(product)

            else:
                product_url = "https://%s:%s@%s/admin/api/%s/products.json" % (
                    api_key, password, store_name, version)
                payload = []
                headers = {
                    'Content-Type': 'application/json'
                }

                response = requests.request("GET", product_url,
                                            headers=headers,
                                            data=payload)
                j = response.json()
                _logger.info(
                    '+++++++++++++++response.json()+++++++++++++++',
                    pprint.pformat(j))
                shopify_products = j['products']
                delay = self.with_delay(priority=1, eta=10)
                delay.import_products_from_shopify(shopify_products)
                _logger.info(
                    '++++++++++products++++++++++++++++++++',
                    pprint.pformat(shopify_products))
                product_link = response.headers[
                    'link'] if 'link' in response.headers else ''
                product_links = product_link.split(',')
                for link in product_links:
                    match = re.compile(r'rel=\"next\"').search(link)
                    if match:
                        product_link = link
                rel = re.search('rel=\"(.*)\"', product_link).group(
                    1) if 'link' in response.headers else ''
                if product_link and rel == 'next':
                    i = 0
                    n = 1
                    while i < n:
                        page_info = re.search('page_info=(.*)>',
                                              product_link).group(1)
                        limit = re.search('limit=(.*)&', product_link).group(1)
                        product_link = "https://%s:%s@%s/admin/api/%s/products.json?limit=%s&page_info=%s" % (
                            api_key, password, store_name, version, limit,
                            page_info)
                        response = requests.request('GET', product_link,
                                                    headers=headers,
                                                    data=payload)
                        j = response.json()
                        _logger.info(
                            '++++++++++++response.json()++++++++++',
                            pprint.pformat(j))
                        if 'products' in j:
                            products = j['products']
                            delay = self.with_delay(priority=1, eta=10)
                            delay.import_products_from_shopify(products)
                        product_link = response.headers['link']
                        product_links = product_link.split(',')
                        for link in product_links:
                            match = re.compile(r'rel=\"next\"').search(link)
                            if match:
                                product_link = link
                        rel = re.search('rel=\"next\"', product_link)
                        i += 1
                        if product_link and rel is not None:
                            n += 1

    def import_products_from_shopify(self, shopify_products):
        """ Method to import products from shopify to odoo.
            Queue job evokes this method for creating products in odoo.

            shopify_products(list):list of dictionary with product details.
        """
        product_tags = []
        shopify_instance = self.shopify_instance_id
        for product in shopify_products:
            exist_products = self.env['product.template'].sudo().search(
                [('shopify_product_id', '=', product['id']),
                 ('shopify_instance_id', '=', shopify_instance.id),
                 ('company_id', '=', shopify_instance.company_id.id)])
            if not exist_products:
                if product['options']:
                    for option in product['options']:
                        attribute_id = self.env[
                            'product.attribute'].sudo().search([
                                ('shopify_attribute_id', '=', option['id']),
                                ('shopify_instance_id', '=',
                                 shopify_instance.id)
                            ])
                        if attribute_id:
                            for opt_val in option['values']:
                                val = attribute_id.value_ids.filtered(
                                    lambda x: x.name == opt_val
                                )
                                if not val:
                                    att_val = {
                                        'name': opt_val
                                    }
                                    attribute_id.sudo().write({
                                        'value_ids': [(0, 0, att_val)]
                                    })
                        else:
                            attribute_id = self.env[
                                'product.attribute'].sudo().create({
                                    'name': option['name'],
                                    'shopify_attribute_id': option['id'],
                                    'shopify_instance_id': shopify_instance.id,

                                })
                            for opt_val in option['values']:
                                att_val = {
                                    'name': opt_val
                                }
                                attribute_id.sudo().write({
                                    'value_ids': [(0, 0, att_val)]
                                })
                if product['tags']:
                    tags = product['tags'].split(',')
                    for rec in tags:
                        product_tag = self.env['product.tag'].search(
                            [('name', '=', rec)]
                        )
                        if product_tag:
                            product_tags.append(product_tag.id)
                        else:
                            product_tag = self.env['product.tag'].create({
                                'name': rec,
                            })
                            product_tags.append(product_tag.id)
                product_id = self.env['product.template'].sudo().create(
                    {
                        'name': product['title'],
                        'type': 'product',
                        'categ_id': self.env.ref(
                            'product.product_category_all').id,
                        'synced_product': True,
                        'default_code': product['variants'][0]['sku'] if
                        product['variants'][0]['sku'] else None,
                        'qty_available': product['variants'][0][
                            'inventory_quantity'] if
                        product['variants'][0][
                            'inventory_quantity'] else None,
                        'description': product['body_html'],
                        'product_tag_ids': product_tags,
                        'shopify_product_id': product['id'],
                        'shopify_instance_id': shopify_instance.id,
                        'company_id': shopify_instance.company_id.id,
                    })
                product_id.shopify_sync_ids.sudo().create({
                    'instance_id': self.shopify_instance_id.id,
                    'shopify_product_id': product['id'],
                    'product_id': product_id.id,
                })
                shopify_price_list = []
                if product['options']:
                    for option in product['options']:
                        attribute_id = self.env[
                            'product.attribute'].sudo().search([
                                ('shopify_attribute_id', '=', option['id']),
                                (
                                    'shopify_instance_id', '=',
                                    shopify_instance.id)
                            ])
                        att_val_ids = self.env[
                            'product.attribute.value'].sudo().search([
                                ('name', 'in', option['values']),
                                ('attribute_id', '=', attribute_id.id)
                            ])
                        att_line = {
                            'attribute_id': attribute_id.id,
                            'value_ids': [(4, att_val.id) for att_val in
                                          att_val_ids]
                        }
                        product_id.sudo().write({
                            'attribute_line_ids': [(0, 0, att_line)]
                        })
                    for shopify_var in product['variants']:
                        shopify_var_list = []
                        shopify_var_id_list = []
                        r = 3
                        for i in range(1, r):
                            if shopify_var['option' + str(i)] is not None:
                                shopify_var_list.append(
                                    shopify_var['option' + str(i)])
                            else:
                                break
                        for option in product['options']:
                            for var in shopify_var_list:
                                if var in option['values']:
                                    attribute_id = self.env[
                                        'product.attribute'].sudo().search(
                                        [
                                            (
                                                'shopify_attribute_id',
                                                '=',
                                                option['id']),
                                            ('shopify_instance_id', '=',
                                             shopify_instance.id)
                                        ])
                                    att_val_id = attribute_id.value_ids.filtered(
                                        lambda x: x.name == var
                                    )
                                    shopify_var_id_list.append(
                                        att_val_id)
                        for variant in product_id.product_variant_ids:
                            o_var_list = variant.product_template_variant_value_ids.mapped(
                                'product_attribute_value_id')
                            o_var_list = [rec for rec in o_var_list]
                            if o_var_list == shopify_var_id_list:
                                variant.sudo().write({
                                    'shopify_variant_id': shopify_var['id'],
                                    'shopify_instance_id': shopify_instance.id,
                                    'synced_product': True,
                                    'company_id': shopify_instance.company_id.id,
                                    'default_code': shopify_var['sku'] if
                                    shopify_var['sku'] else None,
                                    'barcode': shopify_var['barcode'] if
                                    shopify_var['barcode'] else None,
                                    'qty_available': int(
                                        shopify_var['inventory_quantity']),
                                    'lst_price': shopify_var['price']
                                })
                                price_dict = {
                                    shopify_var['id']: shopify_var['price'],
                                    'variant': shopify_var['title']
                                }
                                shopify_price_list.append(price_dict)
                                variant.shopify_sync_ids.sudo().create(
                                    {
                                        'instance_id': shopify_instance.id,
                                        'shopify_product_id':
                                            shopify_var['id'],
                                        'product_prod_id': variant.id,
                                    })
                                variant.shopify_sync_ids.sudo().create(
                                    {
                                        'instance_id': shopify_instance.id,
                                        'shopify_product_id': shopify_var[
                                            'id'],
                                        'product_prod_id': variant.id,
                                    })
                                self.env['stock.quant'].sudo().create({
                                    'location_id': 8,
                                    'product_id': variant.id,
                                    'inventory_quantity': int(
                                        shopify_var['inventory_quantity']),
                                    'inventory_date': fields.date.today(),
                                    'on_hand': True
                                }).action_apply_inventory()
                            elif not o_var_list and \
                                    shopify_var['option2'] is None and \
                                    len(product_id.product_variant_ids) == 1:
                                variant.sudo().write({
                                    'shopify_variant_id': shopify_var[
                                        'id'],
                                    'shopify_instance_id': shopify_instance.id,
                                    'synced_product': True,
                                    'company_id': shopify_instance.company_id.id,
                                    'default_code': shopify_var[
                                        'sku'] if shopify_var[
                                        'sku'] else None,
                                    'barcode': shopify_var['barcode'] if
                                    shopify_var['barcode'] else None,

                                    'qty_available': int(
                                        shopify_var['inventory_quantity']),
                                    'lst_price': shopify_var['price']
                                })
                                price_dict = {
                                    shopify_var['id']: shopify_var['price'],
                                    'variant': shopify_var['title']
                                }
                                shopify_price_list.append(price_dict)
                                variant.shopify_sync_ids.sudo().create(
                                    {
                                        'instance_id': shopify_instance.id,
                                        'shopify_product_id':
                                            shopify_var['id'],
                                        'product_prod_id': variant.id,
                                    })
                                self.env['stock.quant'].sudo().create({
                                    'location_id': 8,
                                    'product_id': variant.id,
                                    'inventory_quantity': int(
                                        shopify_var['inventory_quantity']),
                                    'inventory_date': fields.date.today(),
                                    'on_hand': True
                                }).action_apply_inventory()
                        for image in product['images']:
                            variant = self.env[
                                'product.product'].search([
                                    ('shopify_product_id', '=',
                                     image['product_id'])])
                            src = image['src']
                            image_1920 = base64.b64encode(
                                requests.get(src).content)
                            for i in variant:
                                i.write({
                                    'image_1920': image_1920,
                                })
                    for rec in shopify_price_list:
                        product_product_id = self.env[
                            'product.product'].sudo().search(
                            [('shopify_variant_id', '=', list(rec.keys())[0])])
                        product_attribute_id = self.env[
                            'product.template.attribute.value'].sudo().search(
                            [('ptav_product_variant_ids', '=',
                              product_product_id.id)])
                        default_price = product_product_id.lst_price
                        extra_price = float(
                            list(rec.values())[0]) - default_price
                        product_attribute_id.sudo().write({
                            'price_extra': float(extra_price)
                        })

                else:
                    for variant in product_id.product_variant_ids:
                        variant.sudo().write({
                            'shopify_variant_id': product['id'],
                            'shopify_instance_id': shopify_instance.id,
                            'synced_product': True,
                            'company_id': shopify_instance.company_id.id,
                        })

    def export_products_to_shopify(self, product):
        """ Method to export products from odoo to shopify.
            Queue job evokes this method to export odoo products.

            product(list):list of dictionary with product details.
        """
        api_key = self.shopify_instance_id.con_endpoint
        password = self.shopify_instance_id.consumer_key
        store_name = self.shopify_instance_id.shop_name
        version = self.shopify_instance_id.version
        product_url = "https://%s:%s@%s/admin/api/%s/products.json" % (
            api_key, password, store_name, version)
        product.synced_product = False
        for rec in product:
            if rec.sale_ok:
                instance_ids = rec.shopify_sync_ids.mapped(
                    'instance_id.id')
                if self.shopify_instance_id.id not in instance_ids:
                    variants = []
                    for line in rec.product_variant_ids:
                        line_vals = {
                            "option1": line.partner_ref,
                            "price": line.lst_price,
                            "sku": line.default_code if line.default_code else None,
                            "inventory_quantity": int(
                                line.qty_available),
                            'barcode': line.barcode if line.barcode else None,
                            "id": rec.id,
                            "product_id": rec.id,
                        }
                        variants.append(line_vals)
                    if not variants:
                        line_vals = {
                            "id": rec.id,
                            "product_id": rec.id,
                            "title": rec.name,
                            "body_html": rec.description_sale
                            if rec.description_sale else '',
                            "price": rec.list_price,
                            "sku": rec.default_code if rec.default_code else None,
                            "inventory_quantity": int(
                                rec.qty_available),
                            "unitCost": rec.standard_price,
                            "product_type": 'Storable Product'
                            if rec.type == 'product' else 'Consumable'
                            if rec.type == 'consu' else 'Service',
                        }
                        variants.append(line_vals)
                    payload = json.dumps({
                        "product": {
                            'id': rec.id,
                            "title": rec.name,
                            "body_html": rec.description_sale
                            if rec.description_sale else "",
                            "sku": rec.default_code if rec.default_code else None,
                            "inventory_quantity": int(
                                rec.qty_available),
                            "barcode": rec.barcode if rec.barcode else None,
                            "product_type": 'Storable Product'
                            if rec.type == 'product' else 'Consumable'
                            if rec.type == 'consu' else 'Service',
                            "unitCost": rec.standard_price,
                            "variants": variants,
                        }
                    })
                    headers = {
                        'Content-Type': 'application/json'
                    }
                    response = requests.request("POST", product_url,
                                                headers=headers,
                                                data=payload)
                    response_rec = response.json()
                    response_product_id = response_rec['product']['id']
                    rec.shopify_sync_ids.sudo().create({
                        'instance_id': self.shopify_instance_id.id,
                        'shopify_product_id': response_product_id,
                        'product_id': rec.id,
                    })
                    for prod_variants, items in zip(
                            rec.product_variant_ids,
                            response_rec['product']['variants']):
                        prod_variants.shopify_sync_ids.sudo().create({
                            'instance_id': self.shopify_instance_id.id,
                            'shopify_product_id': items['id'],
                            'product_prod_id': prod_variants.id,
                        })

    def create_product_by_id(self, shopify_instance, api_key, password,
                             store_name, version, product):
        """ Method to create a specific shopify product to odoo by product id.

            shopify_instance(char): id of shopify instance
            api_key(char): api key value
            password(char): password
            store_name(char): name of the shopify store
            version(char):version os shopify store
            product(char): id of the product

            dictionary: returns dictionary of response.
        """
        shopify_instance = shopify_instance
        product_tags = []
        api_key = api_key
        password = password
        store_name = store_name
        version = version
        product = product

        product_url = "https://%s:%s@%s/admin/api/%s/products/%s.json" % (
            api_key, password, store_name, version, product)
        payload = []
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("GET", product_url,
                                    headers=headers,
                                    data=payload)
        j = response.json()
        if 'product' in j:
            product = j['product']
            if product['options']:
                for option in product['options']:
                    attribute_id = self.env[
                        'product.attribute'].sudo().search([
                            ('shopify_attribute_id', '=', option['id']),
                            ('shopify_instance_id', '=', shopify_instance.id)
                        ])
                    if attribute_id:
                        for opt_val in option['values']:
                            val = attribute_id.value_ids.filtered(
                                lambda x: x.name == opt_val
                            )
                            if not val:
                                att_val = {
                                    'name': opt_val
                                }
                                attribute_id.sudo().write({
                                    'value_ids': [(0, 0, att_val)]
                                })
                    else:
                        attribute_id = self.env[
                            'product.attribute'].sudo().create({
                                'name': option['name'],
                                'shopify_attribute_id': option['id'],
                                'shopify_instance_id': shopify_instance.id,

                            })
                        for opt_val in option['values']:
                            att_val = {
                                'name': opt_val
                            }
                            attribute_id.sudo().write({
                                'value_ids': [(0, 0, att_val)]
                            })
            if product['tags']:
                tags = product['tags'].split(',')
                for rec in tags:
                    product_tag = self.env['product.tag'].search(
                        [('name', '=', rec)]
                    )
                    if product_tag:
                        product_tags.append(product_tag.id)
                    else:
                        product_tag = self.env['product.tag'].create({
                            'name': rec,
                        })
                        product_tags.append(product_tag.id)

            product_id = self.env['product.template'].sudo().create({
                'name': product['title'],
                'type': 'product',
                'categ_id': self.env.ref(
                    'product.product_category_all').id,
                'synced_product': True,
                'default_code': product['variants'][0]['sku'] if
                product['variants'][0]['sku'] else None,
                'qty_available': product['variants'][0][
                    'inventory_quantity'] if product['variants'][0][
                    'inventory_quantity'] else None,
                'description': product['body_html'],
                'shopify_product_id': product['id'],
                'shopify_instance_id': shopify_instance.id,
                'company_id': shopify_instance.company_id.id,
            })
            product_id.shopify_sync_ids.sudo().create({
                'instance_id': self.shopify_instance_id.id,
                'shopify_product_id': product['id'],
                'product_id': product_id.id,
            })
            shopify_price_list = []
            if product['options']:
                for option in product['options']:
                    attribute_id = self.env[
                        'product.attribute'].sudo().search([
                            ('shopify_attribute_id', '=', option['id']),
                            ('shopify_instance_id', '=', shopify_instance.id)
                        ])
                    att_val_ids = self.env[
                        'product.attribute.value'].sudo().search([
                            ('name', 'in', option['values']),
                            ('attribute_id', '=', attribute_id.id)
                        ])
                    att_line = {
                        'attribute_id': attribute_id.id,
                        'value_ids': [(4, att_val.id) for att_val in
                                      att_val_ids]
                    }
                    product_id.sudo().write({
                        'attribute_line_ids': [(0, 0, att_line)]
                    })
                for shopify_var in product['variants']:
                    shopify_var_list = []
                    shopify_var_id_list = []
                    r = 3
                    for i in range(1, r):
                        if shopify_var['option' + str(i)] is not None:
                            shopify_var_list.append(
                                shopify_var['option' + str(i)])

                        else:
                            break
                    for option in product['options']:
                        for var in shopify_var_list:
                            if var in option['values']:
                                attribute_id = self.env[
                                    'product.attribute'].sudo().search(
                                    [
                                        ('shopify_attribute_id', '=',
                                         option['id']),
                                        ('shopify_instance_id', '=',
                                         shopify_instance.id)
                                    ])
                                att_val_id = attribute_id.value_ids.filtered(
                                    lambda x: x.name == var
                                )
                                shopify_var_id_list.append(att_val_id)
                    for variant in product_id.product_variant_ids:
                        o_var_list = variant.product_template_variant_value_ids.mapped(
                            'product_attribute_value_id')
                        o_var_list = [rec for rec in o_var_list]
                        if o_var_list == shopify_var_id_list:
                            variant.sudo().write({
                                'shopify_variant_id': shopify_var['id'],
                                'shopify_instance_id': shopify_instance.id,
                                'synced_product': True,
                                'company_id': shopify_instance.company_id.id,
                                'default_code': shopify_var['sku'] if
                                shopify_var['sku'] else None,
                                'qty_available': int(
                                    shopify_var['inventory_quantity']),
                                'barcode': shopify_var['barcode'] if
                                shopify_var['barcode'] else None,
                                'lst_price': shopify_var['price']
                            })
                            price_dict = {
                                shopify_var['id']: shopify_var['price'],
                                'variant': shopify_var['title']
                            }
                            shopify_price_list.append(price_dict)
                            variant.shopify_sync_ids.sudo().create(
                                {
                                    'instance_id': shopify_instance.id,
                                    'shopify_product_id': shopify_var['id'],
                                    'product_prod_id': variant.id,
                                })
                            self.env['stock.quant'].sudo().create({
                                'location_id': 8,
                                'product_id': variant.id,
                                'inventory_quantity': int(
                                    shopify_var['inventory_quantity']),
                                'inventory_date': fields.date.today(),
                                'on_hand': True
                            }).action_apply_inventory()
                        elif not o_var_list and \
                                shopify_var['option2'] is None and len(
                                product_id.product_variant_ids) == 1:
                            variant.sudo().write({
                                'shopify_variant_id': shopify_var['id'],
                                'shopify_instance_id': shopify_instance.id,
                                'synced_product': True,
                                'company_id': shopify_instance.company_id.id,
                                'default_code': shopify_var['sku'] if
                                shopify_var['sku'] else None,
                                'barcode': shopify_var['barcode'] if
                                shopify_var['barcode'] else None,
                                'qty_available': int(
                                    shopify_var['inventory_quantity']),
                                'lst_price': shopify_var['price']
                            })
                            price_dict = {
                                shopify_var['id']: shopify_var['price'],
                                'variant': shopify_var['title']
                            }
                            shopify_price_list.append(price_dict)
                            self.env['stock.quant'].sudo().create({
                                'location_id': 8,
                                'product_id': variant.id,
                                'inventory_quantity': int(
                                    shopify_var['inventory_quantity']),
                                'inventory_date': fields.date.today(),
                                'on_hand': True
                            }).action_apply_inventory()
                            variant.shopify_sync_ids.sudo().create(
                                {
                                    'instance_id': shopify_instance.id,
                                    'shopify_product_id':
                                        shopify_var['id'],
                                    'product_prod_id': variant.id,
                                })
                    for image in product['images']:
                        variant = self.env[
                            'product.product'].search([
                                ('shopify_product_id', '=', image['product_id'])])
                        src = image['src']
                        image_1920 = base64.b64encode(
                            requests.get(src).content)
                        for i in variant:
                            i.write({
                                'image_1920': image_1920,
                            })
                for rec in shopify_price_list:
                    product_product_id = self.env[
                        'product.product'].sudo().search(
                        [('shopify_variant_id', '=', list(rec.keys())[0])])
                    product_attribute_id = self.env[
                        'product.template.attribute.value'].sudo().search(
                        [('ptav_product_variant_ids', '=',
                          product_product_id.id)])
                    default_price = product_product_id.lst_price
                    extra_price = float(
                        list(rec.values())[0]) - default_price
                    product_attribute_id.sudo().write({
                        'price_extra': float(extra_price)
                    })
            else:
                for variant in product_id.product_variant_ids:
                    variant.sudo().write({
                        'shopify_variant_id': product['id'],
                        'shopify_instance_id': shopify_instance.id,
                        'synced_product': True,
                        'company_id': shopify_instance.company_id.id,
                    })
        return response.json()
