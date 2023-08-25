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
import ast
import random
import logging
import requests
import json
from datetime import datetime, timedelta
from odoo import models, fields
from babel.dates import format_date
from odoo.exceptions import ValidationError
from odoo.tools.misc import get_lang
from odoo.http import request

_logger = logging.getLogger(__name__)


class ShopifyConnector(models.Model):
    _name = 'shopify.configuration'
    _description = 'Shopify Connector'
    _rec_name = 'name'

    def _compute_kanban_dashboard(self):
        for shopify_instance in self:
            shopify_instance.kanban_dashboard = json.dumps(
                shopify_instance.get_shopify_configuration_details())

    def _compute_kanban_dashboard_graph(self):
        for shopify_instance in self:
            # if shopify_instance.state == 'new':
            #     shopify_instance.kanban_dashboard_graph = False
            # else:
            shopify_instance.kanban_dashboard_graph = json.dumps(
                shopify_instance.get_graph())

    name = fields.Char(string='Instance Name', required=True)
    con_endpoint = fields.Char(string='API', required=True)
    consumer_key = fields.Char(string='Password', required=True)
    consumer_secret = fields.Char(string='Secret', required=True)
    shop_name = fields.Char(string='Store Name', required=True)
    version = fields.Char(string='Version', required=True)
    last_synced = fields.Datetime(string='Last Synced')
    product_last_synced = fields.Datetime(string='Product Last Synced')
    customer_last_synced = fields.Datetime(string='Customer Last Synced')
    order_last_synced = fields.Datetime(string='Order Last Synced')
    state = fields.Selection([('new', 'Not Connected'),
                              ('sync', 'Connected'), ],
                             'Status', readonly=True, index=True, default='new')
    import_product = fields.Boolean(string='Export Products')
    import_customer = fields.Boolean(string='Export Customers')
    import_order = fields.Boolean(string='Export Orders')
    webhook_product = fields.Char(string='Product Url')
    webhook_customer = fields.Char(string='Customer Url')
    webhook_payment = fields.Char('Payment Url')
    webhook_fulfillment = fields.Char('Fulfillment Url')
    webhook_product_update = fields.Char('Product Update Url')
    webhook_product_delete = fields.Char('Product Delete Url')
    webhook_customer_update = fields.Char('Customer Update Url')
    webhook_customer_delete = fields.Char('Customer Delete Url')

    webhook_order_create = fields.Char('Order Create Url')
    webhook_order_update = fields.Char('Order Update Url')
    webhook_order_Cancel = fields.Char('Order Cancel Url')
    webhook_order_Fulfillment = fields.Char('Order Fulfillment Url')
    webhook_order_Payment = fields.Char('Order Payment Url')
    webhook_order_Refund = fields.Char('Order Refund Url')
    webhook_draft_order_create = fields.Char('Draft Order Create Url')
    webhook_draft_order_update = fields.Char('Draft Order Update Url')
    webhook_draft_order_delete = fields.Char('Draft Order Delete Url')
    webhook_collections = fields.Char('Collections Url')
    webhook_fulfillment_creation = fields.Char('Fulfillment Creation Url')

    company_id = fields.Many2one('res.company', 'Company', required=True)
    customer_ids = fields.One2many('res.partner', 'shopify_instance_id',
                                   string='Customers')
    product_ids = fields.One2many('product.template', 'shopify_instance_id',
                                  string='Products', store=True)
    order_ids = fields.One2many('sale.order', 'shopify_instance_id',
                                string='Orders', store=True)
    log_message_ids = fields.One2many('log.message', 'shopify_instance_id',
                                      string='Logs', store=True)
    customer_count = fields.Integer('Customers', compute='_compute_counts')
    product_count = fields.Integer('Products', compute='_compute_counts')
    order_count = fields.Integer('Orders', compute='_compute_counts')
    log_message_count = fields.Integer('Orders', compute='_compute_counts')
    collection_count = fields.Integer('Collections', compute='_compute_counts')
    kanban_dashboard = fields.Text(compute='_compute_kanban_dashboard')
    kanban_dashboard_graph = fields.Text(
        compute='_compute_kanban_dashboard_graph')
    show_on_dashboard = fields.Boolean('Show on Dashboard', default=True)
    color = fields.Integer('Color', default=0)
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse',
                                   help="Warehouse to update the Inventory of "
                                        "Products")
    active = fields.Boolean('Active', default=True)
    gift_card_count = fields.Integer('Gift Cards', compute='_compute_counts')

    def configure_webhook(self):
        url = request.httprequest.host_url[:-1]
        url = url.replace('http', 'https')
        api_key = self.con_endpoint
        password = self.consumer_key
        store_name = self.shop_name
        version = self.version
        webhooks = [{'topic': 'products/create',
                     'url': '/products'},
                    {'topic': 'products/update',
                     'url': '/update_products'},
                    {'topic': 'products/delete',
                     'url': '/delete_products'},
                    {'topic': 'customers/create',
                     'url': '/customers'},
                    {'topic': 'customers/update',
                     'url': '/update_customer'},
                    {'topic': 'customers/delete',
                     'url': '/delete_customer'},
                    {'topic': 'orders/create',
                     'url': '/create_order'},
                    {'topic': 'orders/updated',
                     'url': '/update_order'},
                    {'topic': 'orders/cancelled',
                     'url': '/cancel_order'},
                    {'topic': 'orders/fulfilled',
                     'url': '/order_fulfillment'},
                    {'topic': 'orders/paid',
                     'url': '/order_payment'},
                    {'topic': 'refunds/create',
                     'url': '/order_refund'},
                    {'topic': 'draft_orders/create',
                     'url': '/draft_orders'},
                    {'topic': 'draft_orders/update',
                     'url': '/draft_order_update'},
                    {'topic': 'draft_orders/delete',
                     'url': '/delete_draft_order'},
                    {'topic': 'collections/create',
                     'url': '/collection_details'},
                    {'topic': 'collections/update',
                     'url': '/collection_details'},
                    {'topic': 'collections/delete',
                     'url': '/collection_details'},
                    {'topic': 'fulfillments/create',
                     'url': '/fulfillment_creation'}
                    ]
        product_url = "https://%s:%s@%s/admin/api/%s/webhooks.json" % (
            api_key, password, store_name, version)
        for record in webhooks:
            address = url + record['url']
            topic = record['topic']
            payload = json.dumps({
                "webhook": {
                    "address": address,
                    "topic": topic,
                    "format": "json",
                }
            })
            headers = {
                'Content-Type': 'application/json'
            }
            requests.request("POST", product_url,
                             headers=headers,
                             data=payload)

    def _compute_counts(self):
        for shopify in self:
            shopify.customer_count = self.env['res.partner'].search_count(
                [('shopify_sync_ids.instance_id', '=', shopify.id)])
            shopify.product_count = self.env['product.template'].search_count(
                [('shopify_sync_ids.instance_id', '=', shopify.id)])
            shopify.order_count = self.env['sale.order'].search_count(
                [('shopify_sync_ids.instance_id', '=', shopify.id)])
            shopify.log_message_count = len(shopify.log_message_ids)
            shopify.collection_count = self.env['collections'].search_count([('shopify_instance_id', '=', shopify.id)])
            shopify.gift_card_count = self.env['product.template'].search_count(
                ['&', ('shopify_sync_ids.instance_id', '=', shopify.id),
                 ('gift_card', '=', True)])

    def shopify_customers(self):
        return {
            'name': 'Shopify Customers',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('shopify_sync_ids.instance_id', '=', self.id)],
            'context': dict(self._context, create=False)
        }

    def shopify_products(self):
        return {
            'name': 'Shopify Products',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'tree,form',
            'domain': [('shopify_sync_ids.instance_id', '=', self.id)],
            'context': dict(self._context, create=False)
        }

    def shopify_orders(self):
        return {
            'name': 'Shopify Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('shopify_sync_ids.instance_id', '=', self.id)],
            'context': dict(self._context, create=False)
        }

    def shopify_log_message(self):
        self.ensure_one()
        if len(self.log_message_ids) > 0:
            return {
                'name': 'Shopify Log Messages',
                'type': 'ir.actions.act_window',
                'res_model': 'log.message',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', self.log_message_ids.ids)],
                'context': dict(self._context, create=False)
            }
        else:
            return {
                'type': 'ir.actions.act_window_close'
            }

    def shopify_collections(self):
        return {
            'name': 'Collections',
            'type': 'ir.actions.act_window',
            'res_model': 'collections',
            'view_mode': 'tree,form',
            'domain': [('shopify_instance_id', '=', self.id)],
            'context': dict(self._context, create=False)
        }

    def shopify_gift_cards(self):
        return {
            'name': 'Shopify Gift Card Products',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'tree,form',
            'domain': ['&', ('shopify_sync_ids.instance_id', '=', self.id),
                       ('gift_card', '=', True)],
            'context': dict(self._context, create=False)
        }

    def sync_shopify(self):
        api_key = self.con_endpoint
        password = self.consumer_key
        store_name = self.shop_name
        version = self.version
        url = "https://%s:%s@%s/admin/api/%s/storefront_access_tokens.json" % (
            api_key, password, store_name, version)
        payload = json.dumps({
            "storefront_access_token": {
                "title": "Test"
            }
        })
        headers = {
            'Content-Type': 'application/json'

        }
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            self.state = "sync"
        else:
            raise ValidationError(
                ("Invalid Credentials provided .Please check them "))

    def sync_shopify_all(self):
        if not self.import_product and not self.import_product and not self.import_order:
            raise ValidationError('Select an Export option from shopify configuration')
        else:
            api_key = self.con_endpoint
            password = self.consumer_key
            store_name = self.shop_name
            version = self.version
            if self.import_product:
                product_url = "https://%s:%s@%s/admin/api/%s/products.json" % (
                    api_key, password, store_name, version)
                self.ensure_one()
                if self.product_last_synced:
                    product = self.env['product.template'].sudo().search(
                        ['&', ('create_date', '>=', self.product_last_synced),
                         ('shopify_sync_ids.instance_id', '!=', self.id)])
                else:
                    synced_products = self.env['shopify.sync'].sudo().search([('instance_id', '=', self.id)]).mapped(
                        'product_id')
                    product = self.env['product.template'].sudo().search([('id', 'not in', synced_products.ids)])
                    for rec in product:
                        variants = []
                        for line in rec.attribute_line_ids.value_ids:
                            line_vals = {
                                "option1": line.name,
                                "price": rec.list_price,
                                "sku": rec.default_code if rec.default_code else None,
                                "barcode": rec.barcode if rec.barcode else None,
                                "inventory_quantity": int(rec.qty_available),
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
                                "inventory_quantity": int(rec.qty_available),
                                "unitCost": rec.standard_price,
                                "product_type": 'Storable Product'
                                if rec.type == 'product' else 'Consumable'
                                if rec.type == 'consu' else 'Service',
                                "barcode": rec.barcode if rec.barcode else None,
                            }
                            variants.append(line_vals)
                        payload = json.dumps({
                            "product": {
                                'id': rec.id,
                                "title": rec.name,
                                "body_html": rec.description_sale
                                if rec.description_sale else "",
                                "sku": rec.default_code if rec.default_code else None,
                                "inventory_quantity": int(rec.qty_available),
                                "product_type": 'Storable Product'
                                if rec.type == 'product' else 'Consumable'
                                if rec.type == 'consu' else 'Service',
                                "unitCost": rec.standard_price,
                                "barcode": rec.barcode if rec.barcode else None,
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
                        rec.shopify_sync_ids.sudo().create({
                            'instance_id': self.id,
                            'shopify_product_id': response_product_id,
                            'product_id': rec.id,
                        })
                    self.product_last_synced = datetime.now()
            if self.import_customer:
                customer_url = "https://%s:%s@%s/admin/api/%s/customers.json" % (
                    api_key, password, store_name, version)
                if self.customer_last_synced:
                    partner = self.env['res.partner'].sudo().search(
                        ['&', ('create_date', '>=', self.customer_last_synced),
                         ('shopify_sync_ids.instance_id', '!=', self.id)])
                else:
                    synced_customers = self.env['shopify.sync'].sudo().search([('instance_id', '=', self.id)]).mapped(
                        'customer_id')

                    partner = self.env['res.partner'].sudo().search([('id', 'not in', synced_customers.ids)])

                    for customer in partner:
                        payload = json.dumps({
                            "customer": {
                                "first_name": customer.name,
                                "last_name": "",
                                "email": customer.email,
                                "phone": customer.phone,
                                "verified_email": True,
                                "addresses": [
                                    {
                                        "address1": customer.street,
                                        "city": customer.city,
                                        "province": "",
                                        "phone": customer.phone,
                                        "zip": customer.zip,
                                        "last_name": "",
                                        "first_name": customer.name,
                                        "country": customer.country_id.name
                                    }
                                ],
                                "send_email_invite": True
                            }
                        })
                        headers = {
                            'Content-Type': 'application/json'
                        }
                        response = requests.request("POST", customer_url,
                                                    headers=headers, data=payload)
                        response_rec = response.json()
                        if response.status_code == 201:
                            response_customer_id = response_rec['customer']['id']
                            customer.shopify_sync_ids.sudo().create({
                                'instance_id': self.id,
                                'shopify_customer_id': response_customer_id,
                                'customer_id': customer.id,
                            })
                    self.customer_last_synced = datetime.now()
            if self.import_order:
                order_url = "https://%s:%s@%s/admin/api/%s/draft_orders.json" % (
                    api_key, password, store_name, version)
                if self.order_last_synced:
                    sale_order = self.env['sale.order'].search(
                        ['&', '&', ('create_date', '>=', self.order_last_synced),
                         ('state', '=', 'draft'),
                         ('shopify_sync_ids.instance_id', '!=', self.id)
                         ])
                else:
                    synced_orders = self.env['shopify.sync'].sudo().search([('instance_id', '=', self.id)]).mapped(
                        'order_id')

                    sale_order = self.env['sale.order'].sudo().search(
                        [('id', 'not in', synced_orders.ids), ('state', '=', 'draft')])


                    for order in sale_order:
                        line_items = []
                        for line in order.order_line:
                            line_vals = {
                                "title": line.product_id.name,
                                "price": line.price_unit,
                                "quantity": int(line.product_uom_qty),
                            }
                            line_items.append(line_vals)
                        payload = json.dumps({
                            "draft_order": {
                                "line_items": line_items,
                                "email": order.partner_id.email,
                                "use_customer_default_address": True
                            }
                        })
                        headers = {
                            'Content-Type': 'application/json'
                        }
                        response = requests.request("POST", order_url,
                                                    headers=headers, data=payload)
                        response_rec = response.json()
                        if response.status_code == 201:
                            response_order_id = response_rec['draft_order']['id']
                            response_status = response_rec['draft_order']['status']
                            response_name = response_rec['draft_order']['name']
                            order.shopify_sync_ids.sudo().create({
                                'instance_id': self.id,
                                'shopify_order_id': response_order_id,
                                'shopify_order_name': response_name,
                                'shopify_order_number': response_order_id,
                                'order_status': response_status,
                                'order_id': order.id,
                                'synced_order': True,
                            })
                            order.shopify_order_id = response_order_id
                    self.order_last_synced = datetime.now()
                self.last_synced = datetime.now()

    def open_shopify_instance(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'shopify_odoo_connector.action_shopify_configuration')
        context = self._context.copy()
        if 'context' in action and type(action['context']) == str:
            context.update(ast.literal_eval(action['context']))
        else:
            context.update(action.get('context', {}))
        action['context'] = context
        action['domain'] = [('id', '=', self.id)]
        return action

    def get_shopify_configuration_details(self):
        customer_count = self.customer_count
        product_count = self.product_count
        sale_count = self.order_count
        sale_income_this_month = 0.0
        sale_income_this_year = 0.0
        sale_income_last_month = 0.0
        return {
            'customer_count': customer_count,
            'product_count': product_count,
            'sale_count': sale_count,
            'sale_income_this_year': sale_income_this_year,
            'sale_income_this_month': sale_income_this_month,
            'sale_income_last_month': sale_income_last_month,
            'company_count': len(self.env.companies),
        }

    def get_graph(self):
        def graph_data(date, amount):
            nm = format_date(date, 'd LLLL Y', locale=locale)
            short_nm = format_date(date, 'd MMM', locale=locale)
            return {'x': short_nm, 'y': amount, 'name': nm}

        data = []
        locale = get_lang(self.env).code
        today = datetime.today()
        for i in range(30, 0, -5):
            current_date = today + timedelta(days=-i)
            data.append(graph_data(current_date, random.randint(-5, 15)))
        return [
            {'values': data, 'title': '', 'key': 'Sale Income', 'area': True,
             'color': '#7c7bad', 'is_sample_data': False}]


class ShopifyPayment(models.Model):
    _name = 'shopify.payment'
    _description = 'Shopify Payments'

    shopify_order_id = fields.Char('Shopify Order Id', readonly=True,
                                   store=True)
    payment_status = fields.Selection([('paid', 'Paid'), ('unpaid', 'Unpaid'),
                                       ('partially_paid', 'Partially Paid'),
                                       ('refunded', 'Refunded'), (
                                           'partially_refunded',
                                           'Partially Refunded')],
                                      string='Payment Status')
    company_id = fields.Many2one('res.company', 'Company')
    shopify_instance_id = fields.Many2one('shopify.configuration',
                                          'Shopify Instance')
