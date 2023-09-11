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
import ast
import json
import logging
import random
import requests
from datetime import datetime, timedelta
from babel.dates import format_date
from odoo import fields, models
from odoo.exceptions import ValidationError
from odoo.tools.misc import get_lang

_logger = logging.getLogger(__name__)


class ShopifyConfiguration(models.Model):
    """Class for shopify.configuration.

        Methods:
            _compute_kanban_dashboard(self):
                Method to compute data for shopify kanban dashboard.
            _compute_kanban_dashboard_graph(self):
                Method to compute shopify kanban dashboard graph.
            _compute_counts(self):
                Method to compute count of data that synced with shopify.
            shopify_customers(self):
                Method to view customers from shopify.
            shopify_products(self):
                Method to view products from shopify
            shopify_orders(self):
                Method to view orders from shopify
            shopify_log_message(self):
                Method to show log messages
            shopify_collection(self):
                Methods to show shopify collection
            shopify_gift_card(self):
                Methode to show shopify gift cards
            sync_shopify(self):
                Method to connect shopify instance.
            sync_shopify_all(self):
                Method of sync all button. Syncs all data from odoo to shopify.
            open_shopify_instance(self):
                Method to open shopify instance by click.
            get_shopify_configuration_details(self):
                Method to get shopify configuration details.
            get_graph(self):
                Method to compute graph values.
    """
    _name = 'shopify.configuration'
    _description = 'Shopify Connector'
    _rec_name = 'name'

    def _compute_kanban_dashboard(self):
        """Method to compute data for shopify kanban dashboard."""
        for shopify_instance in self:
            shopify_instance.kanban_dashboard = json.dumps(
                shopify_instance.get_shopify_configuration_details())

    def _compute_kanban_dashboard_graph(self):
        """Method to compute shopify kanban dashboard graph."""
        for shopify_instance in self:
            shopify_instance.kanban_dashboard_graph = json.dumps(
                shopify_instance.get_graph())

    name = fields.Char(string='Instance Name', required=True,
                       help='Name of the instance')
    con_endpoint = fields.Char(string='API', required=True,
                               help='Consumer end point')
    consumer_key = fields.Char(string='Password', required=True,
                               help='Consumer Key')
    consumer_secret = fields.Char(string='Secret', required=True,
                                  help='Consumer Secret')
    shop_name = fields.Char(string='Store Name', required=True,
                            help='Name of the shop')
    version = fields.Char(string='Version', required=True,
                          help='Version of the shop')
    last_synced = fields.Datetime(string='Last Synced',
                                  help='Last instance synced date')
    product_last_synced = fields.Datetime(string='Product Last Synced',
                                          help='Last product synced date')
    customer_last_synced = fields.Datetime(string='Customer Last Synced',
                                           help='Last customer synced date')
    order_last_synced = fields.Datetime(string='Order Last Synced',
                                        help='Last order synced date')
    state = fields.Selection([('new', 'Not Connected'),
                              ('sync', 'Connected'), ],
                             'Status', readonly=True, index=True,
                             default='new', help='State of shopify instance')
    import_product = fields.Boolean(string='Export Products',
                                    help='Enable to import products.')
    import_customer = fields.Boolean(string='Export Customers',
                                     help='Enable to sync customers')
    import_order = fields.Boolean(string='Export Orders',
                                  help='Enable to sync Orders')
    webhook_product = fields.Char(string='Product Url',
                                  help='Url for create product webhook')
    webhook_customer = fields.Char(string='Customer Url',
                                   help='Url for create customer webhook')
    webhook_payment = fields.Char('Payment Url',
                                  help='Url for create order webhook')
    webhook_fulfillment = fields.Char('Fulfillment Url',
                                      help='Url for create order fulfilment webhook')
    webhook_product_update = fields.Char('Product Update Url',
                                         help='Url for update product webhook')
    webhook_product_delete = fields.Char('Product Delete Url',
                                         help='Url for delete product webhook')
    webhook_customer_update = fields.Char('Customer Update Url',
                                          help='Url for update customer webhook')
    webhook_customer_delete = fields.Char('Customer Delete Url',
                                          help='Url for delete customer webhook')

    webhook_order_create = fields.Char('Order Create Url',
                                       help='Url for create order webhook')
    webhook_order_update = fields.Char('Order Update Url',
                                       help='Url for update order webhook')
    webhook_order_Cancel = fields.Char('Order Cancel Url',
                                       help='Url for cancel order webhook')
    webhook_order_delete = fields.Char('Order Delete Url',
                                       help='Url for order delete webhook')
    webhook_order_Fulfillment = fields.Char('Order Fulfillment Url',
                                            help='Url for order fulfillment webhook')
    webhook_order_Payment = fields.Char('Order Payment Url',
                                        help='Url for order payment webhook')
    webhook_order_Refund = fields.Char('Order Refund Url',
                                       help='Url for order refund webhook')
    webhook_draft_order_create = fields.Char('Draft Order Create Url',
                                             help='Url for create draft order webhook')
    webhook_draft_order_update = fields.Char('Draft Order Update Url',
                                             help='Url for update draft order webhook')
    webhook_draft_order_delete = fields.Char('Draft Order Delete Url',
                                             help='Url for delete draft order webhook')
    webhook_collection = fields.Char('Collections Url',
                                     help='Url for create collection webhook')
    webhook_fulfillment_creation = fields.Char('Fulfillment Creation Url',
                                               help='Url for create product webhook')

    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 help='Company id')
    customer_ids = fields.One2many('res.partner', 'shopify_instance_id',
                                   string='Customers', help='Customer ids')
    product_ids = fields.One2many('product.template', 'shopify_instance_id',
                                  string='Products', store=True,
                                  help='Product ids')
    order_ids = fields.One2many('sale.order', 'shopify_instance_id',
                                string='Orders', store=True, help='Order ids')
    log_message_ids = fields.One2many('log.message', 'shopify_instance_id',
                                      string='Logs', store=True,
                                      help='Log message ids')
    customer_count = fields.Integer('Customer Count',
                                    compute='_compute_counts',
                                    help='Customer count')
    product_count = fields.Integer('Product Count', compute='_compute_counts',
                                   help='Product count')
    order_count = fields.Integer('Order Count', compute='_compute_counts',
                                 help='Order count')
    log_message_count = fields.Integer('Order Log message Count',
                                       compute='_compute_counts',
                                       help='Log message count')
    collection_count = fields.Integer('Collections', compute='_compute_counts',
                                      help='Collection count')
    kanban_dashboard = fields.Text(compute='_compute_kanban_dashboard',
                                   help='field to compute kanban dashboard.')
    kanban_dashboard_graph = fields.Text(
        compute='_compute_kanban_dashboard_graph',
        help='field to compute kanban dashboard graph')
    show_on_dashboard = fields.Boolean('Show on Dashboard', default=True,
                                       help='Will shoe the data on dashboard if enabled.')
    color = fields.Integer('Color', default=0, help='Color number')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse',
                                   help="Warehouse to update the Inventory of "
                                        "Products")
    active = fields.Boolean('Active', default=True, help='Active or not')
    gift_card_count = fields.Integer('Gift Cards', compute='_compute_counts',
                                     help='Count of gift card.')

    def _compute_counts(self):
        """Method to compute count of data that synced with shopify."""
        for shopify in self:
            shopify.customer_count = self.env['res.partner'].search_count(
                [('shopify_sync_ids.instance_id', '=', shopify.id)])
            shopify.product_count = self.env['product.template'].search_count(
                [('shopify_sync_ids.instance_id', '=', shopify.id)])
            shopify.order_count = self.env['sale.order'].search_count(
                [('shopify_sync_ids.instance_id', '=', shopify.id)])
            shopify.log_message_count = len(shopify.log_message_ids)
            shopify.collection_count = self.env['collection'].search_count(
                [('shopify_instance_id', '=', shopify.id)])
            shopify.gift_card_count = self.env[
                'product.template'].search_count(
                ['&', ('shopify_sync_ids.instance_id', '=', shopify.id),
                 ('gift_card', '=', True)])

    def shopify_customers(self):
        """Method to view customers from shopify.
            
            dictionary:returns dictionary with details of ir action act window.
        """
        return {
            'name': 'Shopify Customers',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('shopify_sync_ids.instance_id', '=', self.id)],
            'context': dict(self._context, create=False)
        }

    def shopify_products(self):
        """Method to view products from shopify.
            
            dictionary:returns dictionary with details of ir action act window.
        """
        return {
            'name': 'Shopify Products',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'tree,form',
            'domain': [('shopify_sync_ids.instance_id', '=', self.id)],
            'context': dict(self._context, create=False)
        }

    def shopify_orders(self):
        """Method to view orders from shopify.
            
            dictionary:returns dictionary with details of ir action act window.
        """
        return {
            'name': 'Shopify Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('shopify_sync_ids.instance_id', '=', self.id)],
            'context': dict(self._context, create=False)
        }

    def shopify_log_message(self):
        """Method to view log messages.
            
           dictionary:returns dictionary of action type.
        """
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

    def shopify_collection(self):
        """Method to view shopify collection.
            
            dictionary:returns dictionary with details of ir action act window.
        """
        return {
            'name': 'collection',
            'type': 'ir.actions.act_window',
            'res_model': 'collection',
            'view_mode': 'tree,form',
            'domain': [('shopify_instance_id', '=', self.id)],
            'context': dict(self._context, create=False)
        }

    def shopify_gift_card(self):
        """Method to view shopify gift cards.
            
            dictionary:returns dictionary with details of ir action act window.
        """
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
        """Method to connect shopify instance."""
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
                "Invalid Credentials provided .Please check them ")

    def sync_shopify_all(self):
        """Method of sync all button. Syncs all data from odoo to shopify."""
        if not self.import_product and not self.import_product and not self.import_order:
            raise ValidationError(
                'Select an Export option from shopify configuration')
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
                    synced_products = self.env['shopify.sync'].sudo().search(
                        [('instance_id', '=', self.id)]).mapped(
                        'product_id')
                    product = self.env['product.template'].sudo().search(
                        [('id', 'not in', synced_products.ids)])
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
                                                    headers=headers,
                                                    data=payload)
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
                    synced_customers = self.env['shopify.sync'].sudo().search(
                        [('instance_id', '=', self.id)]).mapped(
                        'customer_id')

                    partner = self.env['res.partner'].sudo().search(
                        [('id', 'not in', synced_customers.ids)])

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
                                                    headers=headers,
                                                    data=payload)
                        response_rec = response.json()
                        if response.status_code == 201:
                            response_customer_id = response_rec['customer'][
                                'id']
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
                        ['&', '&',
                         ('create_date', '>=', self.order_last_synced),
                         ('state', '=', 'draft'),
                         ('shopify_sync_ids.instance_id', '!=', self.id)
                         ])
                else:
                    synced_orders = self.env['shopify.sync'].sudo().search(
                        [('instance_id', '=', self.id)]).mapped(
                        'order_id')

                    sale_order = self.env['sale.order'].sudo().search(
                        [('id', 'not in', synced_orders.ids),
                         ('state', '=', 'draft')])

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
                                                    headers=headers,
                                                    data=payload)
                        response_rec = response.json()
                        if response.status_code == 201:
                            response_order_id = response_rec['draft_order'][
                                'id']
                            response_status = response_rec['draft_order'][
                                'status']
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
        """Method to open shopify instance.
        
          dictionary: returns dictionary of action values
        """
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
        """Method to get shopify configuration details.
        
            dictionary: returns dictionary of configuration values.
        """
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
        """Method to compute graph values.

            dictionary: returns dictionary of values needed for graph.
        """

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
    """Class for model shopify payment"""
    _name = 'shopify.payment'
    _description = 'Shopify Payments'

    shopify_order_id = fields.Char('Shopify Order Id', readonly=True,
                                   store=True, help='Id of shopify order')
    payment_status = fields.Selection([('paid', 'Paid'), ('unpaid', 'Unpaid'),
                                       ('partially_paid', 'Partially Paid'),
                                       ('refunded', 'Refunded'), (
                                           'partially_refunded',
                                           'Partially Refunded')],
                                      string='Payment Status',
                                      help='Status of payment')
    company_id = fields.Many2one('res.company', 'Company', help='Company id')
    shopify_instance_id = fields.Many2one('shopify.configuration',
                                          'Shopify Instance',
                                          help='Id of shopify instance')
