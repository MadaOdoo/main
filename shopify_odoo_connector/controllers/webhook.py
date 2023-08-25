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

from odoo import http
from odoo.http import request
from odoo import SUPERUSER_ID
import logging
import base64
import requests

_logger = logging.getLogger(__name__)


class WebHook(http.Controller):
    @http.route('/products', type='json', auth='none', methods=['POST'],
                csrf=False)
    def get_webhook_url(self):
        """
        Method for creating new products while creating the product in shopify.
        """
        shop_name = request.httprequest.headers.get(
            'X-Shopify-Shop-Domain')
        shopify_instance_id = request.env[
            'shopify.configuration'].with_user(SUPERUSER_ID).search([('shop_name', 'like', shop_name)], limit=1)
        try:
            data = request.jsonrequest
            images = data.get("images")
            image = False
            if images:
                for item in images:
                    src = item['src']
                image = base64.b64encode(requests.get(src).content)
            shop_name = request.httprequest.headers.get(
                'X-Shopify-Shop-Domain')
            shopify_instance_id = request.env[
                'shopify.configuration'].with_user(SUPERUSER_ID).search([
                ('shop_name', 'like', shop_name)
            ], limit=1)
            a = request.jsonrequest['variants']
            if request.jsonrequest['options']:
                for option in request.jsonrequest['options']:
                    attribute_id = request.env['product.attribute'].with_user(
                        SUPERUSER_ID).search([('shopify_attribute_id', '=', option['id']), ('shopify_instance_id', '=', shopify_instance_id.id)])
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
                            SUPERUSER_ID).create({'name': option['name'], 'shopify_attribute_id': option['id'], 'shopify_instance_id': shopify_instance_id.id})
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
                        "name": request.jsonrequest['title'],
                        "type": 'product',
                        'image_1920': image,
                        "categ_id": request.env.ref(
                            'product.product_category_all').id,
                        'description': request.jsonrequest['body_html'],
                        'company_id': shopify_instance_id.company_id.id,
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
                if request.jsonrequest['options']:
                    for option in request.jsonrequest['options']:
                        attribute_id = request.env['product.attribute'].with_user(SUPERUSER_ID).search(
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
                    for shopify_var in request.jsonrequest['variants']:
                        shopify_var_list = []
                        shopify_var_id_list = []
                        r = 3
                        for i in range(1, r):
                            if shopify_var['option' + str(i)] is not None:
                                shopify_var_list.append(
                                    shopify_var['option' + str(i)])
                        for option in request.jsonrequest['options']:
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
                            o_var_list = variant.\
                                product_template_variant_value_ids.mapped(
                                    'product_attribute_value_id')
                            o_var_list = [rec for rec in o_var_list]
                            if o_var_list == shopify_var_id_list:
                                variant.sudo().write({
                                    'shopify_variant_id': shopify_var['id'],
                                    'shopify_instance_id': shopify_instance_id.id,
                                    'company_id':
                                        shopify_instance_id.company_id.id,
                                    'default_code': shopify_var['sku'] if shopify_var['sku'] else None,
                                    'barcode': shopify_var['barcode'] if shopify_var['barcode'] else None,
                                })
                                variant.shopify_sync_ids.sudo().create({
                                    'instance_id': shopify_instance_id.id,
                                    'shopify_product_id': shopify_var['id'],
                                    'product_prod_id': variant.id,
                                })
                else:
                    for variant in product_id.product_variant_ids:
                        variant.sudo().write({
                            'shopify_variant_id': request.jsonrequest['id'],
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

    @http.route('/customers', type='json', auth='none', methods=['POST'],
                csrf=False)
    def get_webhook_customer_url(self, *args, **kwargs):
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
            vals = {}
            if request.jsonrequest['addresses']:
                country_id = request.env['res.country'].sudo().search([
                    (
                        'name', '=',
                        request.jsonrequest['addresses'][0]['country'])
                ])
                state_id = request.env['res.country.state'].sudo().search([
                    ('name', '=',
                     request.jsonrequest['addresses'][0]['province'])
                ])
                vals = {
                    'street': request.jsonrequest['addresses'][0][
                        'address1'],
                    'street2': request.jsonrequest['addresses'][0][
                        'address2'],
                    'city': request.jsonrequest['addresses'][0]['city'],
                    'country_id': country_id.id if country_id else False,
                    'state_id': state_id.id if state_id else False,
                    'zip': request.jsonrequest['addresses'][0]['zip'],
                }
            if request.jsonrequest['first_name']:
                vals['name'] = request.jsonrequest['first_name']
            if request.jsonrequest['last_name']:
                if request.jsonrequest['first_name']:
                    vals['name'] = request.jsonrequest['first_name'] + ' ' + \
                                   request.jsonrequest['last_name']
                else:
                    vals['name'] = request.jsonrequest['last_name']
            if not request.jsonrequest['first_name'] and not \
                    request.jsonrequest[
                        'last_name'] and request.jsonrequest['email']:
                vals['name'] = request.jsonrequest['email']
            vals['email'] = request.jsonrequest['email']
            vals['phone'] = request.jsonrequest['phone']
            vals['company_id'] = shopify_instance_id.company_id.id
            customer_id = request.env['res.partner'].with_user(
                SUPERUSER_ID).search([
                    ('shopify_sync_ids.shopify_customer_id', '=',
                     request.jsonrequest['id']),
                    ('shopify_sync_ids.instance_id', '=',
                     shopify_instance_id.id),
                    ('company_id', 'in',
                     [False, shopify_instance_id.company_id.id])
                ], limit=1)
            if customer_id:
                customer_id.with_user(SUPERUSER_ID).write(vals)
            else:
                customer_id = request.env['res.partner'].\
                    with_user(SUPERUSER_ID).create(vals)
                customer_id.shopify_sync_ids.sudo().create({
                    'instance_id': shopify_instance_id.id,
                    'shopify_customer_id': request.jsonrequest['id'],
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

    @http.route('/draft_orders', type='json', auth='none', methods=['POST'],
                csrf=False)
    def get_webhook_order_url(self, *args, **kwargs):
        data = request.jsonrequest
        shop_name = request.httprequest.headers.get(
            'X-Shopify-Shop-Domain')
        shopify_shop = request.env[
            'shopify.configuration'].with_user(SUPERUSER_ID).search([
                    ('shop_name', 'like',
                     shop_name)
                ], limit=1)
        try:
            shop_name = request.httprequest.headers.get(
                'X-Shopify-Shop-Domain')
            if shop_name == 'nuthousecuracao.myshopify.com':
                shopify_team = request.env.ref('shopify_odoo_connector.sales_team_customers_shopify').id
            else:
                shopify_team = request.env.ref('shopify_odoo_connector.sales_team_business_shopify').id
            shopify_shop = request.env[
                'shopify.configuration'].with_user(SUPERUSER_ID).search([
                                                  ('shop_name', 'like',
                                                   shop_name)
                                                  ], limit=1)
            tax_name = None
            currency = request.env['res.currency'].with_user(
                SUPERUSER_ID).search(
                [
                    ('name', 'ilike', request.jsonrequest['currency']),
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
            if request.jsonrequest['tax_lines']:
                tax = request.jsonrequest['tax_lines'][0]['rate']
                tax_group = request.jsonrequest['tax_lines'][0]['title']
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
                SUPERUSER_ID).search([('shopify_sync_ids.shopify_customer_id',
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
                                  (6, 0, tax_name.ids)] if tax_name else False,
                              }))
            if request.jsonrequest['shipping_line']:
                shipping_lines = request.jsonrequest['shipping_line']
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

    @http.route('/create_order', type='json', auth='none', methods=['POST'],
                csrf=False)
    def get_webhook_create_order_url(self, *args, **kwargs):
        shop_name = request.httprequest.headers.get(
            'X-Shopify-Shop-Domain')
        shopify_shop = request.env[
            'shopify.configuration'].with_user(SUPERUSER_ID).search([
                ('shop_name', 'like',
                    shop_name)], limit=1)
        try:
            data = request.jsonrequest
            shop_name = request.httprequest.headers.get(
                'X-Shopify-Shop-Domain')
            if shop_name == 'nuthousecuracao.myshopify.com':
                shopify_team = request.env.ref('shopify_odoo_connector.sales_team_customers_shopify').id
            else:
                shopify_team = request.env.ref('shopify_odoo_connector.sales_team_business_shopify').id
            shopify_shop = request.env[
                'shopify.configuration'].with_user(SUPERUSER_ID).search([
                                        ('shop_name', 'like',
                                         shop_name)], limit=1)
            tax_name = None
            currency = request.env['res.currency'].with_user(
                SUPERUSER_ID).search(
                [
                    ('name', 'ilike', request.jsonrequest['currency']),
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
            if request.jsonrequest['tax_lines']:
                tax = request.jsonrequest['tax_lines'][0]['rate']
                tax_group = request.jsonrequest['tax_lines'][0]['title']
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
            if request.jsonrequest['shipping_lines']:
                shipping_lines = request.jsonrequest['shipping_lines']
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
                sale_order = request.env['sale.order'].\
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
                                active_ids=
                                sale_order.invoice_ids.id).create({})
                            invoice_pay._create_payments()

            return {'Message': 'Success'}
        except Exception as e:
            request.env['log.message'].sudo().create({
                'name': 'Order Creating not processed',
                'shopify_instance_id': shopify_shop.id,
                'model': 'Sale Order',
            })
            return {'Message': 'Something went Wrong'}
