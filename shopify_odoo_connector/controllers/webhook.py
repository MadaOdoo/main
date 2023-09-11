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
import logging
import requests
from odoo import http
from odoo import SUPERUSER_ID
from odoo.http import request

_logger = logging.getLogger(__name__)


class WebHook(http.Controller):
    """Class for http controller
       
        Methods:
            get_webhook_url(self):
                Method for creating new products while creating the product 
                in shopify.
            get_webhook_update_product_url(self, *args, **kwargs):
                Method for updating  products while updating the product in 
                shopify.
            get_webhook_delete_product_url(self, *args, **kwargs):
                Method for delete  products while deleting the product in 
                shopify.
            get_webhook_customer_url(self, *args, **kwargs):
                Method for creating new customers while creating the customers 
                in shopify.
            get_webhook_update_customer_url(self, *args, **kwargs):
                Method for updating customers while updating the customers in 
                shopify.
            get_webhook_delete_customer_url(self, *args, **kwargs):
                Method for deleting customers while deleting the customers in 
                shopify.
            get_webhook_order_url(self, *args, **kwargs):
                Method for creating new draft orders while creating the draft 
                orders in shopify.
            get_webhook_update_draft_order_url(self, *args, **kwargs):
                Method for updating draft orders while updating draft orders
                in shopify.
            get_webhook_draft_order_delete_url(self, *args, **kwargs):
                Method for deleting draft orders while deleting draft orders 
                in shopify.
            get_webhook_create_order_url(self, *args, **kwargs):
                 Method for creating new orders while creating the orders in 
                 shopify.
            get_webhook_update_order_url(self, *args, **kwargs):
                Method for updating orders while updating orders in shopify.
            get_webhook_cancel_order_url(self, *args, **kwargs):
                Method for canceling orders while canceling the orders in 
                shopify.
            get_webhook_order_delete_url(self, *args, **kwargs):
                Method for deleting orders while deleting the orders in
                shopify.
            get_webhook_order_fulfillment_url(self, *args, **kwargs):
                Method for confirming delivery while confirming delivery in 
                shopify.
            get_webhook_order_payment_url(self, *args, **kwargs):
                Method for confirming payment of orders while confirming 
                payment of orders in shopify.
            get_webhook_order_refund_url(self, *args, **kwargs):
                Method for refund payment of orders while refund payment of 
                orders in shopify.
            get_webhook_collection_details_url(self):
                Method for syncing collection details of shopify into odoo.
            get_webhook_fulfillment_creation(self):
                Method for fulfilment creation of shopify.
    """
    @http.route('/products', type='json', auth='none', methods=['POST'],
                csrf=False)
    def get_webhook_url(self):
        """ Method for creating new products while creating the product in
            shopify.

            dict: returns dictionary of message as success or fail.
        """
        shop_name = request.httprequest.headers.get(
            'X-Shopify-Shop-Domain')
        shopify_instance_id = request.env[
            'shopify.configuration'].with_user(SUPERUSER_ID).search(
            [('shop_name', 'like', shop_name)], limit=1)
        try:
            data = request.get_json_data()
            product_tags = []
            images = data.get("images")
            image = False
            if images:
                for item in images:
                    src = item['src']
                    image = base64.b64encode(requests.get(src).content)
            if data['tags']:
                tags = data['tags'].split(',')
                for rec in tags:
                    product_tag = request.env['product.tag'].with_user(
                        SUPERUSER_ID).search(
                        [('name', '=', rec)]
                    )
                    if product_tag:
                        product_tags.append(product_tag.id)
                    else:
                        product_tag = request.env['product.tag'].with_user(
                            SUPERUSER_ID).create({
                                'name': rec,
                            })
                        product_tags.append(product_tag.id)
            shop_name = request.httprequest.headers.get(
                'X-Shopify-Shop-Domain')
            shopify_instance_id = request.env[
                'shopify.configuration'].with_user(SUPERUSER_ID).search([
                    ('shop_name', 'like', shop_name)
                ], limit=1)
            if data['options']:
                for option in data['options']:
                    attribute_id = request.env['product.attribute'].with_user(
                        SUPERUSER_ID).search(
                        [('shopify_attribute_id', '=', option['id']),
                         ('shopify_instance_id', '=', shopify_instance_id.id)])
                    if attribute_id:
                        for opt_val in option['values']:
                            att_val_ids = attribute_id.value_ids.filtered(
                                lambda x: x.name == opt_val
                            )
                            if not att_val_ids:
                                att_val = {
                                    'name': opt_val
                                }
                                attribute_id.with_user(SUPERUSER_ID).write({
                                    'value_ids': [(0, 0, att_val)]
                                })
                    else:
                        attribute_id = request.env[
                            'product.attribute'].with_user(
                            SUPERUSER_ID).create({'name': option['name'],
                                                  'shopify_attribute_id':
                                                      option['id'],
                                                  'shopify_instance_id': shopify_instance_id.id})
                        for opt_val in option['values']:
                            att_val = {
                                'name': opt_val,
                            }
                            attribute_id.with_user(SUPERUSER_ID).write({
                                'value_ids': [(0, 0, att_val)]
                            })
            product_id = request.env[
                'product.template'].with_user(SUPERUSER_ID).search(
                [
                    ('shopify_sync_ids.shopify_product_id', '=',
                     data.get('id')),
                    ('shopify_sync_ids.instance_id', '=',
                     shopify_instance_id.id),
                    ('company_id', 'in',
                     [shopify_instance_id.company_id.id, False])
                ]).id
            if not product_id:
                product_id = request.env['product.template'].with_user(
                    SUPERUSER_ID).create(
                    {
                        "name": data['title'],
                        "type": 'product',
                        'image_1920': image,
                        "categ_id": request.env.ref(
                            'product.product_category_all').id,
                        'product_tag_ids': product_tags,
                        'description': data['body_html'],
                        'company_id': shopify_instance_id.company_id.id,
                        'default_code': data['variants'][0]['sku'] if
                        data['variants'][0]['sku'] else None,
                        'barcode': data['variants'][0]['barcode'] if
                        data['variants'][0]['barcode'] else None,
                        'list_price': data['variants'][0]['price'] if
                        data['variants'][0]['price'] else None,
                    })
                product_id.shopify_sync_ids.sudo().create({
                    'instance_id': shopify_instance_id.id,
                    'shopify_product_id': data.get('id'),
                    'product_id': product_id.id,
                })
                variants = data.get("variants")
                variant = variants[0]
                fulfillment_service = variant.get("fulfillment_service")
                if fulfillment_service == 'gift_card':
                    product_id.gift_card = True
                else:
                    product_id.gift_card = False
                shopify_price_list = []
                if data['options']:
                    for option in data['options']:
                        attribute_id = request.env[
                            'product.attribute'].with_user(
                            SUPERUSER_ID).search(
                            [
                                ('shopify_attribute_id', '=', option['id']),
                                ('shopify_instance_id', '=',
                                 shopify_instance_id.id)
                            ])
                        att_val_ids = request.env[
                            'product.attribute.value'].with_user(
                            SUPERUSER_ID).search([
                                ('name', 'in', option['values']),
                                ('attribute_id', '=', attribute_id.id)
                            ])
                        att_line = {
                            'attribute_id': attribute_id.id,
                            'value_ids': [(4, att_val.id) for att_val in
                                          att_val_ids]
                        }
                        product_id.with_user(SUPERUSER_ID).write({
                            'attribute_line_ids': [(0, 0, att_line)]
                        })
                    for shopify_var in data['variants']:
                        shopify_var_list = []
                        shopify_var_id_list = []
                        r = 3
                        for i in range(1, r):
                            if shopify_var['option' + str(i)] is not None:
                                shopify_var_list.append(
                                    shopify_var['option' + str(i)])
                        for option in data['options']:
                            for var in shopify_var_list:
                                if var in option['values']:
                                    attribute_id = request.env[
                                        'product.attribute'].sudo().search(
                                        [
                                            ('shopify_attribute_id', '=',
                                             option['id']),
                                            ('shopify_instance_id', '=',
                                             shopify_instance_id.id)
                                        ])
                                    att_val_id = attribute_id.value_ids.filtered(
                                        lambda x: x.name == var
                                    )
                                    shopify_var_id_list.append(att_val_id)
                        for variant in product_id.product_variant_ids:
                            o_var_list = variant. \
                                product_template_variant_value_ids.mapped(
                                    'product_attribute_value_id')
                            o_var_list = [rec for rec in o_var_list]
                            if o_var_list == shopify_var_id_list:
                                variant.sudo().write({
                                    'shopify_variant_id': shopify_var['id'],
                                    'shopify_instance_id': shopify_instance_id.id,
                                    'company_id':
                                        shopify_instance_id.company_id.id,
                                    'default_code': shopify_var['sku'] if
                                    shopify_var['sku'] else None,
                                    'lst_price': shopify_var['price'],
                                    'qty_available': int(
                                        shopify_var['inventory_quantity']),
                                    'weight': shopify_var['weight'],
                                    'barcode': shopify_var['barcode'],
                                })
                                price_dict = {
                                    shopify_var['id']: shopify_var['price'],
                                    'variant': shopify_var['title']
                                }
                                shopify_price_list.append(price_dict)
                                variant.shopify_sync_ids.sudo().create({
                                    'instance_id': shopify_instance_id.id,
                                    'shopify_product_id': shopify_var['id'],
                                    'product_prod_id': variant.id,
                                })
                                request.env[
                                    'stock.quant'].sudo().with_user(
                                    SUPERUSER_ID).create({
                                        'location_id': 8,
                                        'product_id': variant.id,
                                        'inventory_quantity': int(
                                            shopify_var['inventory_quantity']),
                                        'inventory_date': variant.create_date,
                                        'quantity': int(
                                            shopify_var['inventory_quantity']),
                                        'on_hand': True
                                    }).action_apply_inventory()
                    for rec in shopify_price_list:
                        product_product_id = request.env[
                            'product.product'].sudo().search(
                            [('shopify_variant_id', '=', list(rec.keys())[0])])
                        product_attribute_id = request.env[
                            'product.template.attribute.value'].sudo().search([
                                ('ptav_product_variant_ids', '=',
                                 product_product_id.id),
                            ])
                        default_price = product_product_id.lst_price
                        extra_price = float(
                            list(rec.values())[0]) - default_price
                        product_attribute_id.sudo().with_user(
                            SUPERUSER_ID).write({
                                'price_extra': float(extra_price)
                            })
                else:
                    for variant in product_id.product_variant_ids:
                        variant.sudo().write({
                            'shopify_variant_id': data['id'],
                            'shopify_instance_id': shopify_instance_id.id,
                            'company_id': shopify_instance_id.company_id.id,
                        })
                return {"Message": "Success"}
        except Exception as e:
            request.env['log.message'].sudo().create({
                'name': 'Product Creation not processed',
                'shopify_instance_id': shopify_instance_id.id,
                'model': 'Product Template',
            })
            return {"Message": "Something went wrong"}

    @http.route('/update_products', type='json', auth='none', methods=['POST'],
                csrf=False)
    def get_webhook_update_product_url(self, *args, **kwargs):
        """Method for updating  products while updating the product in shopify.

            args(dict):empty dictionary
            kwargs(dict): empty dictionary

            dict: returns dictionary of message as success or fail.
        """
        shop_name = request.httprequest.headers.get(
            'X-Shopify-Shop-Domain')
        shopify_instance_id = request.env[
            'shopify.configuration'].with_user(SUPERUSER_ID).search([
                ('shop_name', 'like', shop_name)
            ], limit=1)
        try:
            data = request.get_json_data()
            product_tags = []
            images = data.get("images")
            image = False
            if images:
                for item in images:
                    src = item['src']
                    image = base64.b64encode(requests.get(src).content)
            if data['tags']:
                tags = data['tags'].split(',')
                for rec in tags:
                    product_tag = request.env['product.tag'].with_user(
                        SUPERUSER_ID).search(
                        [('name', '=', rec)]
                    )
                    if product_tag:
                        product_tags.append(product_tag.id)
                    else:
                        product_tag = request.env['product.tag'].with_user(
                            SUPERUSER_ID).create({
                                'name': rec,
                            })
                        product_tags.append(product_tag.id)
            shop_name = request.httprequest.headers.get(
                'X-Shopify-Shop-Domain')
            shopify_instance_id = request.env[
                'shopify.configuration'].with_user(SUPERUSER_ID).search([
                    ('shop_name', 'like', shop_name)
                ], limit=1)
            product_id = request.env['product.template'].with_user(
                SUPERUSER_ID).search([
                    ('shopify_sync_ids.shopify_product_id', '=',
                     data['id']),
                    ('shopify_sync_ids.instance_id', '=',
                     shopify_instance_id.id),
                    ('company_id', 'in', [False,
                                          shopify_instance_id.company_id.id])
                ])
            if product_id:
                product_id.with_user(SUPERUSER_ID).write({
                    'name': data['title'],
                    'image_1920': image,
                    'company_id': shopify_instance_id.company_id.id,
                    'description': data['body_html'],
                    'product_tag_ids': product_tags,
                    'default_code': data['variants'][0]['sku'] if
                    data['variants'][0]['sku'] else None,
                    'list_price': data['variants'][0]['price'] if
                    data['variants'][0]['price'] else None,
                })
                shopify_price_list = []
                if data['options'] and data['variants']:
                    for shopify_var in data['variants']:
                        request.env['product.product'].with_user(
                            SUPERUSER_ID).search([
                                ('shopify_variant_id', '=', shopify_var['id']),
                                ('shopify_instance_id', '=',
                                 shopify_instance_id.id),
                                ('company_id', '=',
                                 shopify_instance_id.company_id.id),
                            ])
                        for option in data['options']:
                            attribute_id = request.env[
                                'product.attribute'].with_user(
                                SUPERUSER_ID).search([
                                    ('shopify_attribute_id', '=',
                                     option['id']),
                                    ('shopify_instance_id', '=',
                                     shopify_instance_id.id)
                                ])
                            if not attribute_id:
                                attribute_id = request.env[
                                    'product.attribute'].with_user(
                                    SUPERUSER_ID).create({
                                        'name': option['name'],
                                        'shopify_attribute_id':
                                            option['id'],
                                        'shopify_instance_id':
                                            shopify_instance_id.id,
                                    })
                                for opt_val in option['values']:
                                    att_val = {
                                        'name': opt_val
                                    }
                                    attribute_id.with_user(
                                        SUPERUSER_ID).write({
                                            'value_ids': [(0, 0, att_val)]
                                        })
                                    att_val_ids = request.env[
                                        'product.attribute.value'].with_user(
                                        SUPERUSER_ID).search([
                                            ('name', 'in', option['values']),
                                            ('attribute_id', '=',
                                             attribute_id.id)
                                        ])
                                    att_line = {
                                        'attribute_id': attribute_id.id,
                                        'value_ids': [(4, att_val.id) for
                                                      att_val in
                                                      att_val_ids]
                                    }
                                    product_id.with_user(SUPERUSER_ID).write({
                                        'attribute_line_ids': [(0, 0,
                                                                att_line)]
                                    })
                            else:
                                for opt_val in option['values']:
                                    att_val_ids = attribute_id.value_ids.filtered(
                                        lambda x: x.name == opt_val)
                                    if not att_val_ids:
                                        att_val = {
                                            'name': opt_val
                                        }
                                        attribute_id.with_user(
                                            SUPERUSER_ID).write({
                                                'value_ids': [(0, 0, att_val)]
                                            })
                        if data['options']:
                            product_id.write({
                                'attribute_line_ids': [(5,)],
                            })
                            for option in data['options']:
                                attribute_id = request.env[
                                    'product.attribute'].with_user(
                                    SUPERUSER_ID).search(
                                    [
                                        ('shopify_attribute_id',
                                         '=', option['id']),
                                        (
                                            'shopify_instance_id', '=',
                                            shopify_instance_id.id)
                                    ])
                                att_val_ids = request.env[
                                    'product.attribute.value'].with_user(
                                    SUPERUSER_ID).search([
                                        ('name', 'in',
                                         option['values']),
                                        ('attribute_id', '=',
                                         attribute_id.id)
                                    ])
                                att_line = {
                                    'attribute_id': attribute_id.id,
                                    'value_ids': [(4, att_val.id) for
                                                  att_val in
                                                  att_val_ids]
                                }

                                product_id.with_user(SUPERUSER_ID).write({
                                    'attribute_line_ids': [
                                        (0, 0, att_line)]
                                })
                        for shopify_variant in data['variants']:
                            shopify_var_list = []
                            shopify_var_id_list = []
                            r = 4
                            for i in range(1, r):
                                if shopify_variant['option'
                                                   + str(i)] is not None:
                                    shopify_var_list.append(
                                        shopify_variant['option' + str(i)])
                                else:
                                    break
                            for option in data['options']:
                                for variant in shopify_var_list:
                                    if variant in option['values']:
                                        attribute_id = request.env[
                                            'product.attribute'].with_user(
                                            SUPERUSER_ID).search([
                                                ('shopify_attribute_id', '=',
                                                 option['id']),
                                                ('shopify_instance_id', '=',
                                                 shopify_instance_id.id)
                                            ])
                                        att_val_id = attribute_id.value_ids.filtered(
                                            lambda x: x.name == variant
                                        )
                                        shopify_var_id_list.append(
                                            att_val_id)
                            for odoo_var in product_id.product_variant_ids:
                                odoo_var_list = odoo_var.product_template_variant_value_ids.mapped(
                                    'product_attribute_value_id')
                                odoo_var_list = [rec for rec in
                                                 odoo_var_list]
                                if odoo_var_list == shopify_var_id_list:
                                    odoo_var.with_user(SUPERUSER_ID).write(
                                        {
                                            'shopify_variant_id':
                                                shopify_variant['id'],
                                            'shopify_instance_id': shopify_instance_id.id,
                                            'synced_product': True,
                                            'company_id':
                                                shopify_instance_id.company_id.id,
                                            'default_code':
                                                shopify_variant['sku'] if
                                                shopify_variant[
                                                    'sku'] else None,
                                            'lst_price': shopify_variant[
                                                'price'],
                                            'qty_available': int(
                                                shopify_variant[
                                                    'inventory_quantity']),
                                            'weight': shopify_variant[
                                                'weight'],
                                            'barcode': shopify_variant[
                                                'barcode'],
                                        })
                                    price_dict = {
                                        shopify_variant['id']:
                                            shopify_variant[
                                                'price'],
                                        'variant': shopify_variant['title']
                                    }
                                    shopify_price_list.append(price_dict)
                                    stock_quant = request.env[
                                        'stock.quant'].with_user(
                                        SUPERUSER_ID).search(
                                        [('product_id', '=', odoo_var.id)]
                                    )
                                    stock_quant.unlink()
                                    request.env[
                                        'stock.quant'].sudo().with_user(
                                        SUPERUSER_ID).create({
                                            'location_id': 8,
                                            'product_id': odoo_var.id,
                                            'inventory_quantity': int(
                                                shopify_var[
                                                    'inventory_quantity']),
                                            'inventory_date': odoo_var.create_date,
                                            'quantity': int(
                                                shopify_variant[
                                                    'inventory_quantity']),
                                            'on_hand': True
                                        })
            return {'Messages': 'Success'}
        except Exception as e:
            request.env['log.message'].sudo().create({
                'name': 'Product Update not processed',
                'shopify_instance_id': shopify_instance_id.id,
                'model': 'Product Template',
            })
            return {'Message': 'Something went Wrong'}

    @http.route('/product_deleted', type='json', auth='public',
                methods=['POST'],
                csrf=False)
    def get_webhook_delete_product_url(self, *args, **kwargs):
        """Method for delete  products while deleting the product in shopify.

            args(dict):empty dictionary
            kwargs(dict): empty dictionary

            dict: returns dictionary of message as success or fail.
        """
        shop_name = request.httprequest.headers.get(
            'X-Shopify-Shop-Domain')
        shopify_instance_id = request.env[
            'shopify.configuration'].with_user(SUPERUSER_ID).search([
                ('shop_name', 'like', shop_name)
            ], limit=1)
        try:
            shop_name = request.httprequest.headers.get(
                'X-Shopify-Shop-Domain')
            shopify_instance_id = request.env[
                'shopify.configuration'].with_user(SUPERUSER_ID).search([
                    ('shop_name', 'like', shop_name)
                ], limit=1)
            data = request.get_json_data()
            product_id = request.env['product.template'].with_user(
                SUPERUSER_ID).search([
                    ('shopify_sync_ids.shopify_product_id', '=',
                     data['id']),
                    ('shopify_sync_ids.instance_id', '=',
                     shopify_instance_id.id),
                    ('company_id', 'in', [False,
                                          shopify_instance_id.company_id.id])
                ], limit=1)
            if product_id:
                product_id.with_user(SUPERUSER_ID).write({
                    'active': False
                })
            return {'Message': 'Success'}
        except Exception as e:
            request.env['log.message'].sudo().create({
                'name': 'Product Deletion not processed',
                'shopify_instance_id': shopify_instance_id.id,
                'model': 'Product Template',
            })
            return {'Message': 'Something went Wrong'}

    @http.route('/customers', type='json', auth='none', methods=['POST'],
                csrf=False)
    def get_webhook_customer_url(self, *args, **kwargs):
        """ Method for creating new customers while creating the customers in
            shopify.

            args(dict):empty dictionary
            kwargs(dict): empty dictionary

            dict: returns dictionary of message as success or fail.
        """
        shop_name = request.httprequest.headers.get(
            'X-Shopify-Shop-Domain')
        shopify_instance_id = request.env[
            'shopify.configuration'].with_user(SUPERUSER_ID).search([
                ('shop_name', 'like', shop_name)
            ], limit=1)
        try:
            shop_name = request.httprequest.headers.get(
                'X-Shopify-Shop-Domain')
            shopify_instance_id = request.env[
                'shopify.configuration'].with_user(SUPERUSER_ID).search([
                    ('shop_name', 'like', shop_name)
                ], limit=1)
            data = request.get_json_data()
            customer_tags = []
            vals = {}
            if data["tags"]:
                tags = data['tags'].split(',')
                for tag in tags:
                    customer_tag = request.env[
                        'res.partner.category'].with_user(
                        SUPERUSER_ID).search(
                        [('name', '=', tag)])
                    if customer_tag:
                        customer_tags.append(customer_tag.id)
                    else:
                        customer_tag = request.env[
                            'res.partner.category'].with_user(
                            SUPERUSER_ID).create(
                            {'name': tag})
                        customer_tags.append(customer_tag.id)
            if data['addresses']:
                country_id = request.env['res.country'].sudo().search([
                    ('name', '=', data['addresses'][0]['country'])
                ])
                state_id = request.env['res.country.state'].sudo().search([
                    ('name', '=', data['addresses'][0]['province'])
                ])
                vals = {
                    'street': data['addresses'][0]['address1'],
                    'street2': data['addresses'][0]['address2'],
                    'city': data['addresses'][0]['city'],
                    'country_id': country_id.id if country_id else False,
                    'state_id': state_id.id if state_id else False,
                    'zip': data['addresses'][0]['zip'],
                    'category_id': customer_tags,
                }
            if data['first_name']:
                vals['name'] = data['first_name']
            if data['last_name']:
                if data['first_name']:
                    vals['name'] = data['first_name'] + ' ' + \
                                   data['last_name']
                else:
                    vals['name'] = data['last_name']
            if not data['first_name'] and not data['last_name'] and data['email']:
                vals['name'] = data['email']
            vals['email'] = data['email']
            vals['phone'] = data['phone']
            vals['company_id'] = shopify_instance_id.company_id.id
            customer_id = request.env['res.partner'].with_user(
                SUPERUSER_ID).search([
                    ('shopify_sync_ids.shopify_customer_id', '=',
                     data['id']),
                    ('shopify_sync_ids.instance_id', '=',
                     shopify_instance_id.id),
                    ('company_id', 'in',
                     [False, shopify_instance_id.company_id.id])
                ], limit=1)
            if customer_id:
                customer_id.with_user(SUPERUSER_ID).write(vals)
            else:
                customer_id = request.env['res.partner']. \
                    with_user(SUPERUSER_ID).create(vals)
                customer_id.shopify_sync_ids.sudo().create({
                    'instance_id': shopify_instance_id.id,
                    'shopify_customer_id': data['id'],
                    'customer_id': customer_id.id,
                })
            return {"Message": "Success"}
        except Exception as e:
            request.env['log.message'].sudo().create({
                'name': 'Customer Creation not processed',
                'shopify_instance_id': shopify_instance_id.id,
                'model': 'Res Partner',
            })
            return {"Message": "Something went wrong"}

    @http.route('/update_customer', type='json', auth='none', methods=['POST'],
                csrf=False)
    def get_webhook_update_customer_url(self, *args, **kwargs):
        """ Method for updating customers while updating the customers in
            shopify.

            args(dict):empty dictionary
            kwargs(dict): empty dictionary

            dict: returns dictionary of message as success or fail.
        """
        shop_name = request.httprequest.headers.get(
            'X-Shopify-Shop-Domain')
        shopify_instance_id = request.env[
            'shopify.configuration'].with_user(SUPERUSER_ID).search([
                ('shop_name', 'like', shop_name)
            ], limit=1)
        try:
            shop_name = request.httprequest.headers.get(
                'X-Shopify-Shop-Domain')
            shopify_instance_id = request.env[
                'shopify.configuration'].with_user(SUPERUSER_ID).search([
                    ('shop_name', 'like', shop_name)
                ], limit=1)
            data = request.get_json_data()
            customer_tags = []
            vals = {}
            if data["tags"]:
                tags = data['tags'].split(',')
                for tag in tags:
                    customer_tag = request.env[
                        'res.partner.category'].with_user(
                        SUPERUSER_ID).search(
                        [('name', '=', tag)])
                    if customer_tag:
                        customer_tags.append(customer_tag.id)
                    else:
                        customer_tag = request.env[
                            'res.partner.category'].with_user(
                            SUPERUSER_ID).create(
                            {'name': tag})
                        customer_tags.append(customer_tag.id)
            if data['addresses']:
                country_id = request.env['res.country'].sudo().search([
                    ('name', '=', data['addresses'][0]['country'])
                ])
                state_id = request.env['res.country.state'].sudo().search([
                    ('name', '=', data['addresses'][0]['province'])
                ])
                vals = {
                    'street': data['addresses'][0]['address1'],
                    'street2': data['addresses'][0]['address2'],
                    'city': data['addresses'][0]['city'],
                    'country_id': country_id.id if country_id else False,
                    'state_id': state_id.id if state_id else False,
                    'zip': data['addresses'][0]['zip'],
                    'category_id': customer_tags,
                }
            if data['first_name']:
                vals['name'] = data['first_name']
            if data['last_name']:
                if data['first_name']:
                    vals['name'] = data['first_name'] + ' ' + \
                                   data['last_name']
                else:
                    vals['name'] = data['last_name']
            if not data['first_name'] and not data['last_name'] and data['email']:
                vals['name'] = data['email']
            vals['email'] = data['email']
            vals['phone'] = data['phone']
            vals['company_id'] = shopify_instance_id.company_id.id
            customer_id = request.env['res.partner'].with_user(
                SUPERUSER_ID).search([
                    ('shopify_sync_ids.shopify_customer_id', '=',
                     data['id']),
                    ('shopify_sync_ids.instance_id', '=',
                     shopify_instance_id.id),
                    ('company_id', 'in',
                     [False, shopify_instance_id.company_id.id])
                ], limit=1)
            if customer_id:
                customer_id.with_user(SUPERUSER_ID).write(vals)
            else:
                customer_id = request.env['res.partner']. \
                    with_user(SUPERUSER_ID).create(vals)
                customer_id.shopify_sync_ids.sudo().create({
                    'instance_id': shopify_instance_id.id,
                    'shopify_customer_id': data['id'],
                    'customer_id': customer_id.id,
                })
            return {"Message": "Success"}
        except Exception as e:
            request.env['log.message'].sudo().create({
                'name': 'Customer Update not processed',
                'shopify_instance_id': shopify_instance_id.id,
                'model': 'Res Partner',
            })
            return {'Message': 'Something went Wrong'}

    @http.route('/delete_customer', type='json', auth='none', mehtods=['POST'],
                csrf=False)
    def get_webhook_delete_customer_url(self, *args, **kwargs):
        """ Method for deleting customers while deleting the customers in
            shopify.

            args(dict):empty dictionary
            kwargs(dict): empty dictionary

            dict: returns dictionary of message as success or fail.
        """
        shop_name = request.httprequest.headers.get(
            'X-Shopify-Shop-Domain')
        shopify_instance_id = request.env[
            'shopify.configuration'].with_user(SUPERUSER_ID).search([
                ('shop_name', 'like', shop_name)
            ], limit=1)
        try:
            shop_name = request.httprequest.headers.get(
                'X-Shopify-Shop-Domain')
            shopify_instance_id = request.env[
                'shopify.configuration'].with_user(SUPERUSER_ID).search([
                    ('shop_name', 'like', shop_name)
                ], limit=1)
            customer_id = request.env['res.partner'].with_user(
                SUPERUSER_ID).search([
                    ('shopify_sync_ids.shopify_customer_id', '=',
                     request.get_json_data()['id']),
                    ('shopify_sync_ids.instance_id', '=',
                     shopify_instance_id.id),
                    ('company_id', 'in', [False,
                                          shopify_instance_id.company_id.id])
                ], limit=1)
            if customer_id:
                customer_id.with_user(SUPERUSER_ID).write({
                    'active': False,
                })
            return {'Message': 'Success'}
        except Exception as e:
            request.env['log.message'].sudo().create({
                'name': 'Customer Deletion not processed',
                'shopify_instance_id': shopify_instance_id.id,
                'model': 'Res Partner',
            })
            return {'Message': 'Something went Wrong'}

    @http.route('/draft_orders', type='json', auth='none', methods=['POST'],
                csrf=False)
    def get_webhook_order_url(self, *args, **kwargs):
        """ Method for creating new draft orders while creating the draft
            orders in shopify.

            args(dict):empty dictionary
            kwargs(dict): empty dictionary

            dict: returns dictionary of message as success or fail.
        """
        data = request.get_json_data()
        shop_name = request.httprequest.headers.get(
            'X-Shopify-Shop-Domain')
        shopify_shop = request.env[
            'shopify.configuration'].with_user(SUPERUSER_ID).search([
                ('shop_name', 'like',
                 shop_name)
            ], limit=1)
        try:
            exist_order = request.env['shopify.sync'].with_user(
                SUPERUSER_ID).search([
                    ('shopify_order_id', '=', data['id'])
                ])
            if not exist_order:
                shop_name = request.httprequest.headers.get(
                    'X-Shopify-Shop-Domain')
                if shop_name == 'nuthousecuracao.myshopify.com':
                    shopify_team = request.env.ref(
                        'shopify_odoo_connector.sales_team_customers_shopify').id
                else:
                    shopify_team = request.env.ref(
                        'shopify_odoo_connector.sales_team_business_shopify').id
                shopify_shop = request.env[
                    'shopify.configuration'].with_user(SUPERUSER_ID).search([
                        ('shop_name', 'like', shop_name)
                    ], limit=1)
                tax_name = None
                currency = request.env['res.currency'].with_user(
                    SUPERUSER_ID).search(
                    [
                        ('name', 'ilike', data['currency']),
                        ('active', 'in', [False, True]),
                    ])
                if currency and not currency.active:
                    currency.with_user(SUPERUSER_ID).write({
                        'active': True,
                    })
                price_list = request.env[
                    'product.pricelist'].with_user(SUPERUSER_ID).search([
                        ('currency_id', '=', currency.id),
                        ('shopify_instance_id', '=', shopify_shop.id)
                    ])
                if not price_list:
                    price_list = request.env[
                            'product.pricelist'].with_user(SUPERUSER_ID).create({
                                'name': currency.name,
                                'currency_id': currency.id,
                                'shopify_instance_id': shopify_shop.id,
                            })
                if data['tax_lines']:
                    tax = data['tax_lines'][0]['rate']
                    tax_group = data['tax_lines'][0]['title']
                    tax_group_id = request.env[
                        'account.tax.group'].with_user(SUPERUSER_ID).search(
                        [
                            ('name', '=', tax_group)
                        ])
                    taxes = tax * 100
                    tax_name = request.env[
                        'account.tax'].with_user(SUPERUSER_ID).search(
                        [
                            ('amount', '=', taxes),
                            ('tax_group_id', '=', tax_group_id.id),
                            ('type_tax_use', '=', 'sale'),
                            (
                                'company_id', 'in',
                                [shopify_shop.company_id.id, False])
                        ])
                    if not tax_name:
                        tax_group_id = request.env[
                            'account.tax.group'].with_user(
                            SUPERUSER_ID).create(
                            {
                                'name': tax_group,
                            })
                        tax_name = request.env[
                            'account.tax'].with_user(SUPERUSER_ID).create(
                            {
                                'name': tax_group + str(taxes) + '%',
                                'type_tax_use': 'sale',
                                'amount_type': 'percent',
                                'amount': taxes,
                                'tax_group_id': tax_group_id.id,
                                'company_id': shopify_shop.company_id.id,
                            })
                customer_id = data['customer'].get('id')
                customer_name = data['customer'].get(
                    'first_name') + ' ' + data['customer'].get(
                    'last_name')
                partner_id = request.env['res.partner'].with_user(
                    SUPERUSER_ID).search(
                    [('shopify_sync_ids.shopify_customer_id',
                      '=', customer_id),
                     ('shopify_sync_ids.instance_id', '=',
                      shopify_shop.id),
                     ('company_id', 'in',
                      [shopify_shop.company_id.id, False])],
                    limit=1).id
                if not partner_id:
                    partner_id = request.env[
                        'res.partner'].with_user(SUPERUSER_ID).create(
                        {
                            'name': customer_name,
                            'company_id': shopify_shop.company_id.id
                        }).id
                    partner_ = request.env[
                        'res.partner'].with_user(SUPERUSER_ID).browse(
                        partner_id)
                    partner_.shopify_sync_ids.sudo().create({
                        'instance_id': shopify_shop.id,
                        'shopify_customer_id': customer_id,
                        'customer_id': partner_id,
                    })
                vals = []
                line_len = len(data['line_items'])
                for item in data['line_items']:
                    product_shopify_id = item['variant_id'] if item[
                        'variant_id'] else item['product_id']
                    product_id = request.env[
                        'product.product'].with_user(SUPERUSER_ID).search(
                        [
                            ('shopify_sync_ids.shopify_product_id', '=',
                             product_shopify_id),
                            ('shopify_sync_ids.instance_id', '=',
                             shopify_shop.id),
                            ('company_id', 'in',
                             [shopify_shop.company_id.id, False])
                        ]).id
                    if not product_id:
                        product_id = request.env[
                            'product.product'].with_user(SUPERUSER_ID).create(
                            {
                                'name': item['title'],
                                'company_id': shopify_shop.company_id.id,
                                'synced_product': True,
                            }).id
                        product_ = request.env[
                            'product.product'].with_user(SUPERUSER_ID).browse(
                            product_id)
                        product_.shopify_sync_ids.sudo().create({
                            'instance_id': shopify_shop.id,
                            'shopify_product_id': product_shopify_id,
                            'product_prod_id': product_id,
                        })
                    discount_per = 0
                    discount = data.get("applied_discount")
                    if discount:
                        amount = discount.get("amount")
                        dis_amt = float(amount)
                        line_amt = dis_amt / line_len
                        quantity = float(item['quantity'])
                        price = float(item['price'])
                        price_subtotal = quantity * price
                        discount_per = (line_amt / price_subtotal) * 100
                    vals.append((0, 0,
                                 {'product_id': product_id,
                                  'product_uom_qty': item['quantity'],
                                  'price_unit': item['price'],
                                  'currency_id': currency.id,
                                  'discount': discount_per,
                                  'tax_id': [
                                      (6, 0,
                                       tax_name.ids)] if tax_name else False,
                                  }))
                if data['shipping_line']:
                    shipping_lines = data['shipping_line']
                    product_id = request.env.ref(
                        'shopify_odoo_connector.product_shopify_shipping_cost')
                    vals.append((0, 0,
                                 {'product_id': product_id.id,
                                  'product_uom_qty': 1,
                                  'price_unit': shipping_lines['price'],
                                  'tax_id': False,
                                  }))
                so = request.env['sale.order'].with_user(SUPERUSER_ID).create([
                    {'partner_id': partner_id,
                     'shopify_instance_id': shopify_shop.id,
                     'team_id': shopify_team,
                     'pricelist_id': price_list.id,
                     'currency_id': currency.id,
                     'company_id': shopify_shop.company_id.id,
                     'order_line': vals,
                     }, ])
                so.shopify_sync_ids.sudo().create({
                    'instance_id': shopify_shop.id,
                    'shopify_order_id': data['id'],
                    'shopify_order_name': data['name'],
                    'shopify_order_number': data['id'],
                    'order_id': so.id,
                    'synced_order': True,
                })
                so.shopify_order_id = data['id']
                return {"Message": "Success"}
        except Exception as e:
            request.env['log.message'].sudo().create({
                'name': 'Draft Order Creation not processed',
                'shopify_instance_id': shopify_shop.id,
                'model': 'Sale Order',
            })
            return {"Message": "Something went wrong"}

    @http.route('/draft_order_update', type='json', auth='none',
                methods=['POST'], csrf=False)
    def get_webhook_update_draft_order_url(self, *args, **kwargs):
        """ Method for updating draft orders while updating draft orders in
            shopify.

            args(dict):empty dictionary
            kwargs(dict): empty dictionary

            dict: returns dictionary of message as success or fail.
        """
        shop_name = request.httprequest.headers.get(
            'X-Shopify-Shop-Domain')
        shopify_shop = request.env[
            'shopify.configuration'].with_user(SUPERUSER_ID).search([
                ('shop_name', 'like',
                 shop_name)
            ], limit=1)
        try:
            data = request.get_json_data()
            shop_name = request.httprequest.headers.get(
                'X-Shopify-Shop-Domain')
            shopify_shop = request.env[
                'shopify.configuration'].with_user(SUPERUSER_ID).search([
                    ('shop_name', 'like',
                     shop_name)
                ], limit=1)
            sale_order = request.env['sale.order'].with_user(
                SUPERUSER_ID).search(
                [('shopify_sync_ids.shopify_order_id', '=', data['id']),
                 (
                     'shopify_sync_ids.instance_id', '=', shopify_shop.id)])
            tax_name = None
            currency = request.env['res.currency'].with_user(
                SUPERUSER_ID).search(
                [
                    ('name', 'ilike', data['currency']),
                    ('active', 'in', [False, True]),
                ])
            if currency and not currency.active:
                currency.with_user(SUPERUSER_ID).write({
                    'active': True,
                })
            price_list = request.env[
                'product.pricelist'].with_user(SUPERUSER_ID).search([
                    ('currency_id', '=', currency.id),
                    ('shopify_instance_id', '=', shopify_shop.id)
                ])
            if not price_list:
                price_list = request.env[
                    'product.pricelist'].with_user(SUPERUSER_ID).create({
                        'name': currency.name,
                        'currency_id': currency.id,
                        'shopify_instance_id': shopify_shop.id,
                    })
            if data['tax_lines']:
                tax = data['tax_lines'][0]['rate']
                tax_group = data['tax_lines'][0]['title']
                tax_group_id = request.env[
                    'account.tax.group'].with_user(SUPERUSER_ID).search(
                    [
                        ('name', '=', tax_group)
                    ])
                taxes = tax * 100
                tax_name = request.env[
                    'account.tax'].with_user(SUPERUSER_ID).search(
                    [
                        ('amount', '=', taxes),
                        ('tax_group_id', '=', tax_group_id.id),
                        ('type_tax_use', '=', 'sale'),
                        (
                            'company_id', 'in',
                            [shopify_shop.company_id.id, False])
                    ])
                if not tax_name:
                    tax_group_id = request.env[
                        'account.tax.group'].with_user(SUPERUSER_ID).create(
                        {
                            'name': tax_group,
                        })
                    tax_name = request.env[
                        'account.tax'].with_user(SUPERUSER_ID).create(
                        {
                            'name': tax_group + str(taxes) + '%',
                            'type_tax_use': 'sale',
                            'amount_type': 'percent',
                            'amount': taxes,
                            'tax_group_id': tax_group_id.id,
                            'company_id': shopify_shop.company_id.id,
                        })
            customer_id = data['customer'].get('id')
            customer_name = data['customer'].get(
                'first_name') + ' ' + data['customer'].get(
                'last_name')
            partner_id = request.env['res.partner'].with_user(
                SUPERUSER_ID).search(
                [('shopify_sync_ids.shopify_customer_id', '=', customer_id),
                 ('shopify_sync_ids.instance_id', '=',
                  shopify_shop.id),
                 ('company_id', 'in',
                  [shopify_shop.company_id.id, False])],
                limit=1).id
            if not partner_id:
                partner_id = request.env[
                    'res.partner'].with_user(SUPERUSER_ID).create(
                    {
                        'name': customer_name,
                        'company_id': shopify_shop.company_id.id
                    }).id
                partner_ = request.env[
                    'res.partner'].with_user(SUPERUSER_ID).browse(partner_id)
                partner_.shopify_sync_ids.sudo().create({
                    'instance_id': shopify_shop.id,
                    'shopify_customer_id': customer_id,
                    'customer_id': partner_id,
                })
            vals = []
            line_len = len(data['line_items'])
            for item in data['line_items']:
                product_shopify_id = item['variant_id'] if item[
                    'variant_id'] else item['product_id']
                product_id = request.env[
                    'product.product'].with_user(SUPERUSER_ID).search(
                    [
                        ('shopify_sync_ids.shopify_product_id', '=',
                         product_shopify_id),
                        ('shopify_sync_ids.instance_id', '=', shopify_shop.id),
                        ('company_id', 'in',
                         [shopify_shop.company_id.id, False])
                    ]).id
                if not product_id:
                    product_id = request.env[
                        'product.product'].with_user(SUPERUSER_ID).create(
                        {
                            'name': item['title'],
                            'company_id': shopify_shop.company_id.id,
                            'synced_product': True,
                        }).id
                    product_ = request.env[
                        'product.product'].with_user(SUPERUSER_ID).browse(
                        product_id)
                    product_.shopify_sync_ids.sudo().create({
                        'instance_id': shopify_shop.id,
                        'shopify_product_id': product_shopify_id,
                        'product_prod_id': product_id,
                    })
                discount_per = 0
                discount = data.get("applied_discount")
                if discount:
                    amount = discount.get("amount")
                    dis_amt = float(amount)
                    line_amt = dis_amt / line_len
                    quantity = float(item['quantity'])
                    price = float(item['price'])
                    price_subtotal = quantity * price
                    discount_per = (line_amt / price_subtotal) * 100

                vals.append((0, 0,
                             {'product_id': product_id,
                              'product_uom_qty': item['quantity'],
                              'price_unit': item['price'],
                              'currency_id': currency.id,
                              'discount': discount_per,
                              'tax_id': [
                                  (6, 0, tax_name.ids)] if tax_name else False,
                              }))
            if data['shipping_line']:
                shipping_lines = data['shipping_line']
                product_id = request.env.ref(
                    'shopify_odoo_connector.product_shopify_shipping_cost')
                vals.append((0, 0,
                             {'product_id': product_id.id,
                              'product_uom_qty': 1,
                              'price_unit': shipping_lines['price'],
                              'tax_id': False,
                              }))
            sale_order.order_line = False
            sale_order.with_user(SUPERUSER_ID).write(
                {'partner_id': partner_id,
                 'shopify_instance_id': shopify_shop.id,
                 'pricelist_id': price_list.id,
                 'currency_id': currency.id,
                 'company_id': shopify_shop.company_id.id,
                 'order_line': vals,
                 })
            line = sale_order.shopify_sync_ids.sudo().create({
                'instance_id': shopify_shop.id,
                'shopify_order_id': data['id'],
                'shopify_order_name': data['name'],
                'order_id': sale_order.id,
                'synced_order': True,
            })
            sale_order.shopify_order_id = data['id']
            if data['status']:
                if sale_order:
                    line.sudo().write({
                        'order_status': data['status'],
                    })
            if data['order_id']:
                if sale_order:
                    line.sudo().write({
                        'last_order_id': data['order_id'],
                    })
            return {'Message': 'Success'}
        except Exception as e:
            request.env['log.message'].sudo().create({
                'name': 'Draft Order Update not processed',
                'shopify_instance_id': shopify_shop.id,
                'model': 'Sale Order',
            })
            return {'Message': 'Something went Wrong'}

    @http.route('/delete_draft_order', type='json', auth='none',
                methods=['POST'], csrf=False)
    def get_webhook_draft_order_delete_url(self, *args, **kwargs):
        """ Method for deleting draft orders while deleting draft orders in
            shopify.

            args(dict):empty dictionary
            kwargs(dict): empty dictionary

            dict: returns dictionary of message as success or fail.
        """
        shop_name = request.httprequest.headers.get(
            'X-Shopify-Shop-Domain')
        shopify_instance_id = request.env[
            'shopify.configuration'].with_user(SUPERUSER_ID).search([
                ('shop_name', 'like', shop_name)
            ], limit=1)
        try:
            shop_name = request.httprequest.headers.get(
                'X-Shopify-Shop-Domain')
            shopify_instance_id = request.env[
                'shopify.configuration'].with_user(SUPERUSER_ID).search([
                    ('shop_name', 'like', shop_name)
                ], limit=1)
            order_id = request.env['sale.order'].with_user(
                SUPERUSER_ID).search([
                    ('shopify_sync_ids.shopify_order_id', '=',
                     request.get_json_data()['id']),
                    ('shopify_sync_ids.instance_id', '=',
                     shopify_instance_id.id)
                ])
            if order_id:
                order_id.unlink()
            return {'Message': 'Success'}
        except Exception as e:
            request.env['log.message'].sudo().create({
                'name': 'Draft Order Delete not processed',
                'shopify_instance_id': shopify_instance_id.id,
                'model': 'Sale Order',
            })
            return {'Message': 'Something went Wrong'}

    @http.route('/create_order', type='json', auth='none', methods=['POST'],
                csrf=False)
    def get_webhook_create_order_url(self, *args, **kwargs):
        """ Method for creating new orders while creating the orders in
            shopify.

            args(dict):empty dictionary
            kwargs(dict): empty dictionary

            dict: returns dictionary of message as success or fail.
        """
        shop_name = request.httprequest.headers.get(
            'X-Shopify-Shop-Domain')
        shopify_shop = request.env[
            'shopify.configuration'].with_user(SUPERUSER_ID).search([
                ('shop_name', 'like',
                 shop_name)], limit=1)
        try:
            data = request.get_json_data()
            shop_name = request.httprequest.headers.get(
                'X-Shopify-Shop-Domain')
            if shop_name == 'nuthousecuracao.myshopify.com':
                shopify_team = request.env.ref(
                    'shopify_odoo_connector.sales_team_customers_shopify').id
            else:
                shopify_team = request.env.ref(
                    'shopify_odoo_connector.sales_team_business_shopify').id
            shopify_shop = request.env[
                'shopify.configuration'].with_user(SUPERUSER_ID).search([
                    ('shop_name', 'like',
                     shop_name)], limit=1)
            tax_name = None
            currency = request.env['res.currency'].with_user(
                SUPERUSER_ID).search(
                [
                    ('name', 'ilike', data['currency']),
                    ('active', 'in', [False, True]),
                ])
            if currency and not currency.active:
                currency.with_user(SUPERUSER_ID).write({
                    'active': True,
                })
            price_list = request.env[
                'product.pricelist'].with_user(SUPERUSER_ID).search([
                    ('currency_id', '=', currency.id),
                    ('shopify_instance_id', '=', shopify_shop.id)
                ])
            if not price_list:
                price_list = request.env[
                    'product.pricelist'].with_user(SUPERUSER_ID).create({
                        'name': currency.name,
                        'currency_id': currency.id,
                        'shopify_instance_id': shopify_shop.id,
                    })
            if data['tax_lines']:
                tax = data['tax_lines'][0]['rate']
                tax_group = data['tax_lines'][0]['title']
                tax_group_id = request.env[
                    'account.tax.group'].with_user(SUPERUSER_ID).search(
                    [
                        ('name', '=', tax_group)
                    ])
                taxes = tax * 100
                tax_name = request.env[
                    'account.tax'].with_user(SUPERUSER_ID).search(
                    [
                        ('amount', '=', taxes),
                        ('tax_group_id', '=', tax_group_id.id),
                        ('type_tax_use', '=', 'sale'),
                        (
                            'company_id', 'in',
                            [shopify_shop.company_id.id, False])
                    ])
                if not tax_name:
                    tax_group_id = request.env[
                        'account.tax.group'].with_user(SUPERUSER_ID).create(
                        {
                            'name': tax_group,
                        })
                    tax_name = request.env[
                        'account.tax'].with_user(SUPERUSER_ID).create(
                        {
                            'name': tax_group + str(taxes) + '%',
                            'type_tax_use': 'sale',
                            'amount_type': 'percent',
                            'amount': taxes,
                            'tax_group_id': tax_group_id.id,
                            'company_id': shopify_shop.company_id.id,
                        })
            customer_id = data['customer'].get('id')
            customer_name = data['customer'].get(
                'first_name') + ' ' + data['customer'].get(
                'last_name')
            partner_id = request.env['res.partner'].with_user(
                SUPERUSER_ID).search(
                [('shopify_sync_ids.shopify_customer_id', '=', customer_id),
                 ('shopify_sync_ids.instance_id', '=',
                  shopify_shop.id),
                 ('company_id', 'in',
                  [shopify_shop.company_id.id, False])],
                limit=1).id
            if not partner_id:
                partner_id = request.env[
                    'res.partner'].with_user(SUPERUSER_ID).create(
                    {
                        'name': customer_name,
                        'company_id': shopify_shop.company_id.id
                    }).id
                partner_ = request.env[
                    'res.partner'].with_user(SUPERUSER_ID).browse(partner_id)
                partner_.shopify_sync_ids.sudo().create({
                    'instance_id': shopify_shop.id,
                    'shopify_customer_id': customer_id,
                    'customer_id': partner_id,
                })
            vals = []
            line_len = len(data['line_items'])
            for item in data['line_items']:
                product_shopify_id = item['variant_id'] if item[
                    'variant_id'] else item['product_id']
                product_id = request.env[
                    'product.product'].with_user(SUPERUSER_ID).search(
                    [
                        ('shopify_sync_ids.shopify_product_id', '=',
                         product_shopify_id),
                        ('shopify_sync_ids.instance_id', '=', shopify_shop.id),
                        ('company_id', 'in',
                         [shopify_shop.company_id.id, False])
                    ]).id
                if not product_id:
                    product_id = request.env[
                        'product.product'].with_user(SUPERUSER_ID).create(
                        {
                            'name': item['title'],
                            'company_id': shopify_shop.company_id.id,
                            'synced_product': True,
                        }).id
                    product_ = request.env[
                        'product.product'].with_user(SUPERUSER_ID).browse(
                        product_id)
                    product_.shopify_sync_ids.sudo().create({
                        'instance_id': shopify_shop.id,
                        'shopify_product_id': product_shopify_id,
                        'product_prod_id': product_id,
                    })
                discount_per = 0
                discount = data.get("discount_applications")
                if discount:
                    for items in discount:
                        amount = items.get("value")
                        dis_amt = float(amount)
                        line_amt = dis_amt / line_len
                        quantity = float(item['quantity'])
                        price = float(item['price'])
                        price_subtotal = quantity * price
                        discount_per = (line_amt / price_subtotal) * 100
                vals.append((0, 0,
                             {'product_id': product_id,
                              'product_uom_qty': item['quantity'],
                              'price_unit': item['price'],
                              'currency_id': currency.id,
                              'discount': discount_per,
                              'tax_id': [
                                  (6, 0, tax_name.ids)] if tax_name else False,
                              }))
            if data['shipping_lines']:
                shipping_lines = data['shipping_lines']
                product_id = request.env.ref(
                    'shopify_odoo_connector.product_shopify_shipping_cost')
                for line in shipping_lines:
                    vals.append((0, 0,
                                 {'product_id': product_id.id,
                                  'product_uom_qty': 1,
                                  'price_unit': line['price'],
                                  'tax_id': False,
                                  }))
            if data["payment_terms"]:
                payment_term = data["payment_terms"]
                term_id = request.env['account.payment.term'].with_user(
                    SUPERUSER_ID).search([
                        ('name', 'like', payment_term['payment_terms_name'])
                    ])
                if not term_id:
                    term_id = request.env['account.payment.term'].with_user(
                        SUPERUSER_ID).create({
                            'name': payment_term['payment_terms_name'],
                        })
                sale_order = request.env['sale.order'].with_user(
                    SUPERUSER_ID).create([
                        {'partner_id': partner_id,
                         'pricelist_id': price_list.id,
                         'payment_term_id': term_id.id,
                         'team_id': shopify_team,
                         'state': 'sent',
                         'currency_id': currency.id,
                         'company_id': shopify_shop.company_id.id,
                         'order_line': vals,
                         }, ])
                sale_order.shopify_sync_ids.sudo().create({
                    'instance_id': shopify_shop.id,
                    'shopify_order_id': data['id'],
                    'shopify_order_name': data['name'],
                    'order_id': sale_order.id,
                    'synced_order': True,
                })
                sale_order.shopify_order_id = data['id']
                payment_id = request.env['shopify.payment'].with_user(
                    SUPERUSER_ID).search([
                        ('shopify_order_id', '=', data['id']),
                        ('shopify_instance_id', '=', shopify_shop.id)])
                if payment_id:
                    if payment_id.payment_status == 'paid':
                        sale_order.state = 'sale'
                        sale_order._create_invoices()
                        if sale_order.invoice_ids:
                            sale_order.invoice_ids.action_post()
                            sale_order.invoice_ids.action_register_payment()
                            invoice_pay = request.env[
                                'account.payment.register'].with_user(
                                SUPERUSER_ID).with_context(
                                active_model='account.move',
                                active_ids=sale_order.invoice_ids.id).create(
                                {})
                            invoice_pay._create_payments()
            else:
                sale_order = request.env['sale.order']. \
                    with_user(SUPERUSER_ID).create([
                        {'partner_id': partner_id,
                         'pricelist_id': price_list.id,
                         'state': 'sent',
                         'currency_id': currency.id,
                         'company_id': shopify_shop.company_id.id,
                         'order_line': vals,
                         }, ])
                sale_order.shopify_sync_ids.sudo().create({
                    'instance_id': shopify_shop.id,
                    'shopify_order_id': data['id'],
                    'shopify_order_name': data['name'],
                    'order_id': sale_order.id,
                    'synced_order': True,
                })
                sale_order.shopify_order_id = data['id']
                payment_id = request.env['shopify.payment'].with_user(
                    SUPERUSER_ID).search([
                        ('shopify_order_id', '=', data['id']),
                        ('shopify_instance_id', '=',
                         shopify_shop.id)])
                if payment_id:
                    if payment_id.payment_status == 'paid':
                        sale_order.state = 'sale'
                        sale_order._create_invoices()
                        if sale_order.invoice_ids:
                            sale_order.invoice_ids.action_post()
                            sale_order.invoice_ids.action_register_payment()
                            invoice_pay = request.env[
                                'account.payment.register'].with_user(
                                SUPERUSER_ID).with_context(
                                active_model='account.move',
                                active_ids=sale_order.invoice_ids.id).create({})
                            invoice_pay._create_payments()
            return {'Message': 'Success'}
        except Exception as e:
            request.env['log.message'].sudo().create({
                'name': 'Order Creating not processed',
                'shopify_instance_id': shopify_shop.id,
                'model': 'Sale Order',
            })
            return {'Message': 'Something went Wrong'}

    @http.route('/update_order', type='json', auth='none', methods=['POST'],
                csrf=False)
    def get_webhook_update_order_url(self, *args, **kwargs):
        """ Method for updating orders while updating orders in shopify.

            args(dict):empty dictionary
            kwargs(dict): empty dictionary

            dict: returns dictionary of message as success or fail.
        """
        shop_name = request.httprequest.headers.get(
            'X-Shopify-Shop-Domain')
        shopify_shop = request.env[
            'shopify.configuration'].with_user(SUPERUSER_ID).search([
                ('shop_name', 'like',
                 shop_name)], limit=1)
        try:
            data = request.get_json_data()
            shop_name = request.httprequest.headers.get(
                'X-Shopify-Shop-Domain')
            shopify_shop = request.env[
                'shopify.configuration'].with_user(SUPERUSER_ID).search([
                    ('shop_name', 'like',
                     shop_name)], limit=1)
            sale_order = request.env['sale.order']. \
                with_user(SUPERUSER_ID). \
                search([('shopify_sync_ids.shopify_order_id', '=', data['id']),
                        ('shopify_sync_ids.instance_id', '=',
                         shopify_shop.id)])
            tax_name = None
            currency = request.env['res.currency'].with_user(
                SUPERUSER_ID).search(
                [
                    ('name', 'ilike', request.get_json_data()['currency']),
                    ('active', 'in', [False, True]),
                ])
            if currency and not currency.active:
                currency.with_user(SUPERUSER_ID).write({
                    'active': True,
                })
            price_list = request.env[
                'product.pricelist'].with_user(SUPERUSER_ID).search([
                    ('currency_id', '=', currency.id),
                    ('shopify_instance_id', '=', shopify_shop.id)
                ])
            if not price_list:
                price_list = request.env[
                    'product.pricelist'].with_user(SUPERUSER_ID).create({
                        'name': currency.name,
                        'currency_id': currency.id,
                        'shopify_instance_id': shopify_shop.id,
                    })
            if request.get_json_data()['tax_lines']:
                tax = request.get_json_data()['tax_lines'][0]['rate']
                tax_group = request.get_json_data()['tax_lines'][0]['title']
                tax_group_id = request.env[
                    'account.tax.group'].with_user(SUPERUSER_ID).search(
                    [
                        ('name', '=', tax_group)
                    ])
                taxes = tax * 100
                tax_name = request.env[
                    'account.tax'].with_user(SUPERUSER_ID).search(
                    [
                        ('amount', '=', taxes),
                        ('tax_group_id', '=', tax_group_id.id),
                        ('type_tax_use', '=', 'sale'),
                        (
                            'company_id', 'in',
                            [shopify_shop.company_id.id, False])
                    ])
                if not tax_name:
                    tax_group_id = request.env[
                        'account.tax.group'].with_user(SUPERUSER_ID).create(
                        {
                            'name': tax_group,
                        })
                    tax_name = request.env[
                        'account.tax'].with_user(SUPERUSER_ID).create(
                        {
                            'name': tax_group + str(taxes) + '%',
                            'type_tax_use': 'sale',
                            'amount_type': 'percent',
                            'amount': taxes,
                            'tax_group_id': tax_group_id.id,
                            'company_id': shopify_shop.company_id.id,
                        })
            customer_id = data['customer'].get('id')
            customer_name = data['customer'].get(
                'first_name') + ' ' + data['customer'].get(
                'last_name')
            partner_id = request.env['res.partner'].with_user(
                SUPERUSER_ID).search(
                [('shopify_sync_ids.shopify_customer_id', '=', customer_id),
                 ('shopify_sync_ids.instance_id', '=',
                  shopify_shop.id),
                 ('company_id', 'in',
                  [shopify_shop.company_id.id, False])],
                limit=1).id
            if not partner_id:
                partner_id = request.env[
                    'res.partner'].with_user(SUPERUSER_ID).create(
                    {
                        'name': customer_name,
                        'company_id': shopify_shop.company_id.id
                    }).id
                partner_ = request.env[
                    'res.partner'].with_user(SUPERUSER_ID).browse(partner_id)
                partner_.shopify_sync_ids.sudo().create({
                    'instance_id': shopify_shop.id,
                    'shopify_customer_id': customer_id,
                    'customer_id': partner_id,
                })
            vals = []
            line_len = len(data['line_items'])
            for item in data['line_items']:
                product_shopify_id = item['variant_id'] if item[
                    'variant_id'] else item['product_id']
                product_id = request.env[
                    'product.product'].with_user(SUPERUSER_ID).search(
                    [
                        ('shopify_sync_ids.shopify_product_id', '=',
                         product_shopify_id),
                        ('shopify_sync_ids.instance_id', '=', shopify_shop.id),
                        ('company_id', 'in',
                         [shopify_shop.company_id.id, False])
                    ]).id
                if not product_id:
                    product_id = request.env[
                        'product.product'].with_user(SUPERUSER_ID).create(
                        {
                            'name': item['title'],
                            'company_id': shopify_shop.company_id.id,
                            'synced_product': True,
                        }).id
                    product_ = request.env[
                        'product.product'].with_user(SUPERUSER_ID).browse(
                        product_id)
                    product_.shopify_sync_ids.sudo().create({
                        'instance_id': shopify_shop.id,
                        'shopify_product_id': product_shopify_id,
                        'product_prod_id': product_id,
                    })
                discount_per = 0
                discount = data.get("discount_applications")
                if discount:
                    for items in discount:
                        amount = items.get("value")
                        dis_amt = float(amount)
                        line_amt = dis_amt / line_len
                        quantity = float(item['quantity'])
                        price = float(item['price'])
                        price_subtotal = quantity * price
                        discount_per = (line_amt / price_subtotal) * 100
                if item['fulfillable_quantity'] != 0 or \
                        item['fulfillment_status'] == 'fulfilled':
                    vals.append((0, 0,
                                 {'product_id': product_id,
                                  'product_uom_qty': item['quantity'],
                                  'price_unit': item['price'],
                                  'currency_id': currency.id,
                                  'discount': discount_per,
                                  'tax_id': [
                                      (6, 0, tax_name.ids)] if tax_name
                                  else False,
                                  }))
            if request.get_json_data()['shipping_lines']:
                shipping_lines = request.get_json_data()['shipping_lines']
                product_id = request.env.ref(
                    'shopify_odoo_connector.product_shopify_shipping_cost')
                for line in shipping_lines:
                    vals.append((0, 0,
                                 {'product_id': product_id.id,
                                  'product_uom_qty': 1,
                                  'price_unit': line['price'],
                                  'tax_id': False,
                                  }))
            if vals:
                if data["payment_terms"]:
                    payment_term = data["payment_terms"]
                    term_id = request.env['account.payment.term'].with_user(
                        SUPERUSER_ID).search([
                            ('name', 'like', payment_term['payment_terms_name'])
                        ])
                    if not term_id:
                        term_id = request.env['account.payment.term']. \
                            with_user(SUPERUSER_ID).create({
                                'name': payment_term['payment_terms_name'],
                            })
                    sale_order.order_line = False
                    sale_order.with_user(SUPERUSER_ID).write(
                        {'partner_id': partner_id,
                         'payment_term_id': term_id.id,
                         'pricelist_id': price_list.id,
                         'currency_id': currency.id,
                         'company_id': shopify_shop.company_id.id,
                         'order_line': vals,
                         })
                else:
                    sale_order.order_line = False
                    sale_order.with_user(SUPERUSER_ID).write(
                        {'partner_id': partner_id,
                         'pricelist_id': price_list.id,
                         'currency_id': currency.id,
                         'company_id': shopify_shop.company_id.id,
                         'order_line': vals,
                         })
            return {'Message': 'Success'}
        except Exception as e:
            request.env['log.message'].sudo().create({
                'name': 'Order Updating not processed',
                'shopify_instance_id': shopify_shop.id,
                'model': 'Sale Order',
            })
            return {'Message': 'Something went Wrong'}

    @http.route('/cancel_order', type='json', auth='none', methods=['POST'],
                csrf=False)
    def get_webhook_cancel_order_url(self, *args, **kwargs):
        """ Method for canceling orders while canceling the orders in shopify.

            args(dict):empty dictionary
            kwargs(dict): empty dictionary

            dict: returns dictionary of message as success or fail.
        """
        shop_name = request.httprequest.headers.get(
            'X-Shopify-Shop-Domain')
        shopify_instance_id = request.env[
            'shopify.configuration'].with_user(SUPERUSER_ID).search([
                ('shop_name', 'like', shop_name)
            ], limit=1)
        try:
            shop_name = request.httprequest.headers.get(
                'X-Shopify-Shop-Domain')
            shopify_instance_id = request.env[
                'shopify.configuration'].with_user(SUPERUSER_ID).search([
                    ('shop_name', 'like', shop_name)
                ], limit=1)
            order_id = request.env['sale.order'].with_user(
                SUPERUSER_ID).search([
                    ('shopify_sync_ids.shopify_order_id', '=',
                     request.get_json_data()['id']),
                    ('shopify_sync_ids.instance_id', '=',
                     shopify_instance_id.id)
                ])
            if order_id:
                order_id.state = 'cancel'
            return {'Message': 'Success'}
        except Exception as e:
            request.env['log.message'].sudo().create({
                'name': 'Order Cancellation not processed',
                'shopify_instance_id': shopify_instance_id.id,
                'model': 'Sale Order',
            })
            return {'Message': 'Something went Wrong'}

    @http.route('/delete_order', type='json', auth='none',
                methods=['POST'], csrf=False)
    def get_webhook_order_delete_url(self, *args, **kwargs):
        """
            Method for deleting orders while deleting the orders in shopify.
        """
        shop_name = request.httprequest.headers.get(
            'X-Shopify-Shop-Domain')
        shopify_instance_id = request.env[
            'shopify.configuration'].with_user(SUPERUSER_ID).search([
                ('shop_name', 'like', shop_name)
            ], limit=1)
        try:
            shop_name = request.httprequest.headers.get(
                'X-Shopify-Shop-Domain')
            shopify_instance_id = request.env[
                'shopify.configuration'].with_user(SUPERUSER_ID).search([
                    ('shop_name', 'like', shop_name)
                ], limit=1)
            order_id = request.env['sale.order'].with_user(
                SUPERUSER_ID).search([
                    ('shopify_sync_ids.shopify_order_id', '=',
                     request.get_json_data()['id']),
                    ('shopify_sync_ids.instance_id', '=',
                     shopify_instance_id.id)
                ])
            if order_id:
                order_id.state = 'cancel'
                order_id.unlink()
            return {'Message': 'Success'}
        except Exception as e:
            request.env['log.message'].sudo().create({
                'name': 'Draft Order Delete not processed',
                'shopify_instance_id': shopify_instance_id.id,
                'model': 'Sale Order',
            })
            return {'Message': 'Something went Wrong'}

    @http.route('/order_fulfillment', type='json', auth='none',
                methods=['POST'], csrf=False)
    def get_webhook_order_fulfillment_url(self, *args, **kwargs):
        """ Method for confirming delivery while confirming delivery in
            shopify.

            args(dict):empty dictionary
            kwargs(dict): empty dictionary

            dict: returns dictionary of message as success or fail.
        """
        shop_name = request.httprequest.headers.get(
            'X-Shopify-Shop-Domain')
        shopify_instance_id = request.env[
            'shopify.configuration'].with_user(SUPERUSER_ID).search([
                ('shop_name', 'like', shop_name)
            ], limit=1)
        try:
            if request.get_json_data()['id']:
                data = request.get_json_data()
                shop_name = request.httprequest.headers.get(
                    'X-Shopify-Shop-Domain')
                shopify_instance_id = request.env[
                    'shopify.configuration'].with_user(SUPERUSER_ID).search([
                        ('shop_name', 'like', shop_name)
                    ], limit=1)
                fulfillment_status = request.get_json_data()[
                    'fulfillment_status']
                order_id = request.env['sale.order'].with_user(
                    SUPERUSER_ID).search([
                        ('shopify_sync_ids.shopify_order_id', '=',
                         request.get_json_data()['id']),
                        ('shopify_sync_ids.instance_id', '=',
                         shopify_instance_id.id)
                    ])
                if fulfillment_status == 'fulfilled':
                    if order_id.state == 'draft' or order_id.state == 'sent':
                        order_id.state = 'sale'
                        order_id._action_confirm()
                    elif order_id.state == 'sale':
                        order_id._action_confirm()
                    if order_id.picking_ids:
                        pick_order = order_id.picking_ids
                        move_lines = data.get("fulfillments")
                        for record in move_lines:
                            for rec in record['line_items']:
                                product_shopify_id = rec['variant_id'] if \
                                    rec[
                                        'variant_id'] else rec['product_id']
                                product_id = request.env[
                                    'product.product'].with_user(
                                    SUPERUSER_ID).search(
                                    [
                                        ('shopify_sync_ids.shopify_product_id',
                                         '=', product_shopify_id),
                                        ('shopify_sync_ids.instance_id', '=',
                                         shopify_instance_id.id),
                                        ('company_id', 'in',
                                         [shopify_instance_id.company_id.id,
                                          False])
                                    ]).id
                                if not product_id:
                                    product_id = request.env[
                                        'product.product'].with_user(
                                        SUPERUSER_ID).create(
                                        {
                                            'name': rec['title'],
                                            'company_id':
                                                shopify_instance_id.company_id.id,
                                        }).id
                                    product_ = request.env[
                                        'product.product'].with_user(
                                        SUPERUSER_ID).browse(
                                        product_id)
                                    product_.shopify_sync_ids.sudo().create({
                                        'instance_id': shopify_instance_id.id,
                                        'shopify_product_id':
                                            product_shopify_id,
                                        'product_prod_id': product_id,
                                    })
                                quantity = rec['quantity']
                                for recs in pick_order:
                                    for records in recs.move_ids_without_package:
                                        if records.product_id.id == product_id:
                                            records.with_user(
                                                SUPERUSER_ID).write({
                                                    'quantity_done': quantity,
                                                })
                                    recs.immediate_transfer = True
                                    recs.button_validate()
                elif fulfillment_status == 'partially_fulfilled':
                    if order_id.state == 'draft' or order_id.state == 'sent':
                        order_id.state = 'sale'
                        order_id._action_confirm()
                    elif order_id.state == 'sale':
                        order_id._action_confirm()
                    if order_id.picking_ids:
                        pick_order = order_id.picking_ids
                        move_lines = data.get("fulfillments")
                        for record in move_lines:
                            for rec in record['line_items']:
                                product_shopify_id = rec['variant_id'] if \
                                    rec[
                                        'variant_id'] else rec['product_id']
                                product_id = request.env[
                                    'product.product'].with_user(
                                    SUPERUSER_ID).search(
                                    [
                                        ('shopify_sync_ids.shopify_product_id',
                                         '=',
                                         product_shopify_id),
                                        ('shopify_sync_ids.instance_id', '=',
                                         shopify_instance_id.id),
                                        ('company_id', 'in',
                                         [shopify_instance_id.company_id.id,
                                          False])
                                    ]).id
                                if not product_id:
                                    product_id = request.env[
                                        'product.product'].with_user(
                                        SUPERUSER_ID).create(
                                        {
                                            'name': rec['title'],
                                            'company_id':
                                                shopify_instance_id.company_id.id,
                                        }).id
                                    product_ = request.env[
                                        'product.product'].with_user(
                                        SUPERUSER_ID).browse(
                                        product_id)
                                    product_.shopify_sync_ids.sudo().create({
                                        'instance_id': shopify_instance_id.id,
                                        'shopify_product_id':
                                            product_shopify_id,
                                        'product_prod_id': product_id,
                                    })
                                quantity = rec['quantity']
                                for recs in pick_order:
                                    for records in recs.move_ids_without_package:
                                        if records.product_id.id == product_id:
                                            records.with_user(
                                                SUPERUSER_ID).write({
                                                    'quantity_done': quantity,
                                                })
                                    recs.immediate_transfer = True
                                    recs.button_validate()
            return {'Message': 'Success'}
        except Exception as e:
            request.env['log.message'].sudo().create({
                'name': 'Order Fulfillment Creation not processed',
                'shopify_instance_id': shopify_instance_id.id,
                'model': 'Stock Picking',
            })
            return {'Message': 'Something went Wrong'}

    @http.route('/order_payment', type='json', auth='none', methods=['POST'],
                csrf=False)
    def get_webhook_order_payment_url(self, *args, **kwargs):
        """ Method for confirming payment of orders while confirming payment
            of orders in shopify.

            args(dict):empty dictionary
            kwargs(dict): empty dictionary

            dict: returns dictionary of message as success or fail.
        """
        shop_name = request.httprequest.headers.get(
            'X-Shopify-Shop-Domain')
        shopify_instance_id = request.env[
            'shopify.configuration'].with_user(SUPERUSER_ID).search([
                ('shop_name', 'like', shop_name)
            ], limit=1)
        try:
            if request.get_json_data()['id']:
                shop_name = request.httprequest.headers.get(
                    'X-Shopify-Shop-Domain')
                shopify_instance_id = request.env[
                    'shopify.configuration'].with_user(SUPERUSER_ID).search([
                        ('shop_name', 'like', shop_name)
                    ], limit=1)
                payment_status = request.get_json_data()['financial_status']
                order_id = request.env['sale.order'].with_user(
                    SUPERUSER_ID).search([
                        ('shopify_sync_ids.shopify_order_id', '=',
                         request.get_json_data()['id']),
                        ('shopify_sync_ids.instance_id', '=',
                         shopify_instance_id.id)])
                if order_id:
                    order_id.with_user(SUPERUSER_ID).write({
                        'payment_status': 'paid' if payment_status == 'paid'
                        else 'partially_paid'
                        if payment_status == 'partially_paid'
                        else 'partially_refunded'
                        if payment_status == 'partially_refunded'
                        else 'refunded' if payment_status == 'refunded'
                        else 'unpaid',
                    })
                    if payment_status == 'paid':
                        if order_id.state == 'draft' or order_id.state == \
                                'sent':
                            order_id.state = 'sale'
                            order_id._create_invoices()
                        elif order_id.state == 'sale':
                            order_id._create_invoices()
                        if order_id.invoice_ids:
                            order_id.invoice_ids.action_post()
                            order_id.invoice_ids.action_register_payment()
                            invoice_pay = request.env[
                                'account.payment.register'].with_user(
                                SUPERUSER_ID).with_context(
                                active_model='account.move',
                                active_ids=order_id.invoice_ids.id).create({})
                            invoice_pay._create_payments()
                    request.env['shopify.payment'].with_user(
                        SUPERUSER_ID).create({
                            'shopify_order_id': request.get_json_data()['id'],
                            'payment_status': 'paid' if
                            payment_status == 'paid'
                            else 'partially_paid'
                            if payment_status == 'partially_paid'
                            else 'partially_refunded'
                            if payment_status == 'partially_refunded'
                            else 'refunded' if payment_status == 'refunded'
                            else 'unpaid',
                            'company_id': shopify_instance_id.company_id.id,
                            'shopify_instance_id': shopify_instance_id.id,
                        })
                else:
                    request.env['shopify.payment'].with_user(
                        SUPERUSER_ID).create({
                            'shopify_order_id': request.get_json_data()['id'],
                            'payment_status': 'paid' if
                            payment_status == 'paid'
                            else 'partially_paid'
                            if payment_status == 'partially_paid'
                            else 'partially_refunded'
                            if payment_status == 'partially_refunded'
                            else 'refunded' if payment_status == 'refunded'
                            else 'unpaid',
                            'company_id': shopify_instance_id.company_id.id,
                            'shopify_instance_id': shopify_instance_id.id,
                        })
            return {'Message': 'Success'}
        except Exception as e:
            request.env['log.message'].sudo().create({
                'name': 'Order Payment Creation not processed',
                'shopify_instance_id': shopify_instance_id.id,
                'model': 'Account Move',
            })
            return {'Message': 'Something went Wrong'}

    @http.route('/order_refund', type='json', auth='none', methods=['POST'],
                csrf=False)
    def get_webhook_order_refund_url(self, *args, **kwargs):
        """ Method for refund payment of orders while refund payment of orders
            in shopify.

            args(dict):empty dictionary
            kwargs(dict): empty dictionary

            dict: returns dictionary of message as success or fail.
        """
        shop_name = request.httprequest.headers.get(
            'X-Shopify-Shop-Domain')
        shopify_instance_id = request.env[
            'shopify.configuration'].with_user(SUPERUSER_ID).search([
                ('shop_name', 'like', shop_name)
            ], limit=1)
        try:
            data = request.get_json_data()
            shop_name = request.httprequest.headers.get(
                'X-Shopify-Shop-Domain')
            shopify_instance_id = request.env[
                'shopify.configuration'].with_user(SUPERUSER_ID).search([
                    ('shop_name', 'like', shop_name)
                ], limit=1)
            order_id = request.env['sale.order'].with_user(
                SUPERUSER_ID).search([
                    ('shopify_sync_ids.shopify_order_id', '=',
                     request.get_json_data()['order_id']),
                    ('shopify_sync_ids.instance_id', '=',
                     shopify_instance_id.id)
                ])
            invoice = order_id.invoice_ids
            credit_note = request.env[
                'account.move.reversal'].with_user(
                SUPERUSER_ID).with_context(
                {'active_ids': [invoice.id], 'active_id': invoice.id,
                 'active_model': 'account.move'}).create({
                    'date_mode': 'entry',
                    'reason': 'shopify refund',
                    'journal_id': invoice.journal_id.id,
                    })
            invoice_ref = credit_note.reverse_moves()
            invoice_refund = request.env['account.move'].with_user(
                SUPERUSER_ID).browse(invoice_ref['res_id'])
            vals = []
            i = 0
            for rec in data["refund_line_items"]:
                record = rec["line_item"]
                product_shopify_id = record['variant_id'] if \
                    record[
                        'variant_id'] else record['product_id']
                product_id = request.env[
                    'product.product'].with_user(
                    SUPERUSER_ID).search(
                    [
                        ('shopify_sync_ids.shopify_product_id',
                         '=',
                         product_shopify_id),
                        ('shopify_sync_ids.instance_id', '=',
                         shopify_instance_id.id),
                        ('company_id', 'in',
                         [shopify_instance_id.company_id.id,
                          False])
                    ]).id
                if not product_id:
                    product_id = request.env[
                        'product.product'].with_user(
                        SUPERUSER_ID).create(
                        {
                            'name': record['title'],
                            'company_id': shopify_instance_id.company_id.id,
                        }).id
                    product_ = request.env[
                        'product.product'].with_user(
                        SUPERUSER_ID).browse(
                        product_id)
                    product_.shopify_sync_ids.sudo().create({
                        'instance_id': shopify_instance_id.id,
                        'shopify_product_id': product_shopify_id,
                        'product_prod_id': product_id,
                    })
                if record['tax_lines']:
                    tax_lines = record['tax_lines']
                    tax_line = tax_lines[i]
                    price = float(tax_line['price']) + float(record['price'])
                    i += 1
                else:
                    price = record['price']
                vals.append((0, 0,
                             {'product_id': product_id,
                              'name': record['title'],
                              'quantity': record['quantity'],
                              'price_unit': price,
                              }))
            if invoice_refund:
                invoice_refund.action_post()
                invoice_refund.button_draft()
                invoice_refund.invoice_line_ids = False
                invoice_refund.sudo().write({
                    'invoice_line_ids': vals,
                })
                invoice_refund.action_post()
                invoice_refund.action_register_payment()
                credit_note_pay = request.env[
                    'account.payment.register'].with_user(
                    SUPERUSER_ID).with_context(
                    active_model='account.move',
                    active_ids=invoice_refund.id).create({})
                credit_note_pay._create_payments()
                inv_id = order_id.invoice_ids.id
                ids = []
                for rec in invoice_refund.invoice_line_ids:
                    ids.append(rec.id)
                for record in order_id.order_line.invoice_lines:
                    ids.append(record.id)
                order_id.sudo().write({
                    'invoice_ids': [(4, invoice_refund.id), (4, inv_id)],
                })
                order_id.order_line.invoice_lines = [(6, False, ids)]
            return {'Message': 'Success'}
        except Exception as e:
            request.env['log.message'].sudo().create({
                'name': 'Order Refund Creation not processed',
                'shopify_instance_id': shopify_instance_id.id,
                'model': 'Account Move',
            })
            return {'Message': 'Something went Wrong'}

    @http.route('/collection_details', type='json', auth='none',
                methods=['POST'], csrf=False)
    def get_webhook_collection_details_url(self):
        """ Method for syncing collection details of shopify into odoo.

            dict: returns dictionary of message as success or fail.
        """
        shop_name = request.httprequest.headers.get(
            'X-Shopify-Shop-Domain')
        shopify_instance_id = request.env[
            'shopify.configuration'].sudo().search([
                ('shop_name', 'like', shop_name)
            ], limit=1)
        try:
            data = request.get_json_data()
            shop_name = request.httprequest.headers.get(
                'X-Shopify-Shop-Domain')
            event_type = request.httprequest.headers.get(
                'X-Shopify-Topic')
            shopify_instance_id = request.env[
                'shopify.configuration'].sudo().search([
                    ('shop_name', 'like', shop_name)
                ], limit=1)
            if event_type == 'collection/create':
                collection = request.env['collection'].sudo().search([
                    ('collection_id', '=', data['id']),
                    ('shopify_instance_id', '=', shopify_instance_id.id),
                ])
                if not collection:
                    request.env['collection'].sudo().create(
                        {
                            'name': data['title'],
                            'collection_id': data['id'],
                            'shopify_instance_id': shopify_instance_id.id,
                        }
                    )
                else:
                    request.env['collection'].sudo().write(
                        {
                            'name': data['title'],
                        }
                    )
            elif event_type == 'collection/update':
                collection = request.env['collection'].sudo().search([
                    ('collection_id', '=', data['id']),
                    ('shopify_instance_id', '=', shopify_instance_id.id),
                ])
                if not collection:
                    request.env['collection'].sudo().create(
                        {
                            'name': data['title'],
                            'collection_id': data['id'],
                            'shopify_instance_id': shopify_instance_id.id,
                        }
                    )
                else:
                    request.env['collection'].sudo().write(
                        {
                            'name': data['title'],
                        }
                    )
            elif event_type == 'collection/delete':
                collection = request.env['collection'].sudo().search([
                    ('collection_id', '=', data['id']),
                    ('shopify_instance_id', '=', shopify_instance_id.id),
                ])
                if collection:
                    collection.active = False
            return {'Message': 'Success'}
        except Exception as e:
            request.env['log.message'].sudo().create({
                'name': 'Collection details creation not processed',
                'shopify_instance_id': shopify_instance_id.id,
                'model': 'collection',
            })
            return {'Message': 'Something went Wrong'}

    @http.route('/fulfillment_creation', type='json', auth='none',
                methods=['POST'], csrf=False)
    def get_webhook_fulfillment_creation(self):
        """ Method for fulfilment creation of shopify.

            dict: returns dictionary of message as success or fail.
        """
        shop_name = request.httprequest.headers.get(
            'X-Shopify-Shop-Domain')
        shopify_instance_id = request.env[
            'shopify.configuration'].with_user(SUPERUSER_ID).search([
                ('shop_name', 'like', shop_name)
            ], limit=1)
        try:
            if request.get_json_data()['id']:
                data = request.get_json_data()
                shop_name = request.httprequest.headers.get(
                    'X-Shopify-Shop-Domain')
                shopify_instance_id = request.env[
                    'shopify.configuration'].with_user(SUPERUSER_ID).search([
                        ('shop_name', 'like', shop_name)
                    ], limit=1)
                order_id = request.env['sale.order'].with_user(
                    SUPERUSER_ID).search([
                        ('shopify_sync_ids.shopify_order_id', '=',
                         request.get_json_data()['order_id']),
                        ('shopify_sync_ids.instance_id', '=',
                         shopify_instance_id.id)
                    ])
                if order_id.state == 'draft' or order_id.state == 'sent':
                    order_id.state = 'sale'
                    order_id._action_confirm()
                elif order_id.state == 'sale':
                    order_id._action_confirm()
                if order_id.picking_ids:
                    pick_order = order_id.picking_ids
                    move_lines = data.get("line_items")
                    for rec in move_lines:
                        product_shopify_id = rec['variant_id'] if \
                            rec[
                                'variant_id'] else rec['product_id']
                        product_id = request.env[
                            'product.product'].with_user(
                            SUPERUSER_ID).search(
                            [
                                ('shopify_sync_ids.shopify_product_id',
                                 '=',
                                 product_shopify_id),
                                ('shopify_sync_ids.instance_id', '=',
                                 shopify_instance_id.id),
                                ('company_id', 'in',
                                 [shopify_instance_id.company_id.id,
                                  False])
                            ]).id
                        if not product_id:
                            product_id = request.env[
                                'product.product'].with_user(
                                SUPERUSER_ID).create(
                                {
                                    'name': rec['title'],
                                    'company_id':
                                        shopify_instance_id.company_id.id,
                                }).id
                            product_ = request.env[
                                'product.product'].with_user(
                                SUPERUSER_ID).browse(
                                product_id)
                            product_.shopify_sync_ids.sudo().create({
                                'instance_id': shopify_instance_id.id,
                                'shopify_product_id': product_shopify_id,
                                'product_prod_id': product_id,
                            })
                        quantity = rec['quantity']
                        for record in pick_order:
                            for recs in record.move_ids_without_package:
                                if recs.product_id.name == rec['title']:
                                    recs.quantity_done = float(quantity)
            return {'Message': 'Success'}
        except Exception as e:
            request.env['log.message'].sudo().create({
                'name': 'Fulfillment Creation not processed',
                'shopify_instance_id': shopify_instance_id.id,
                'model': 'Stock Picking',
            })
            return {'Message': 'Something went Wrong'}
