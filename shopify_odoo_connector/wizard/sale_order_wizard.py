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
import dateutil.parser
import json
import logging
import pprint
import pytz
import re
import requests
import odoo
from odoo import models, fields
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class OrderWizard(models.TransientModel):
    """ Class for transient model order wizard
        
        Methods:
            sync_orders(self):
                method to create queue job for exporting orders.It will also
                call the methods to create queue jobs for importing orders.
            sync_confirmed_orders(self):
                method to create queue jobs for importing confirmed orders.
            sync_draft_orders(self):
                method to create queue jobs for importing draft orders.
            import_confirmed_orders_from_shopify(self,shopify_orders):
                method to import confirmed orders from shopify to odoo.
                Queue job evokes this method for creating confirmed orders
                in odoo.
            import_draft_orders_from_shopify(self,shopify_orders):
                method to import draft orders from shopify to odoo.Queue job
                evokes this method for creating draft orders in odoo.
            export_orders_to_shopify(self,sale_order):
                method to export orders from odoo to shopify.Queue job
                evokes this method to export odoo orders.
    """
    _name = 'order.wizard'
    _description = 'Order Wizard'

    import_orders = fields.Selection(string='Import/Export',
                                     selection=[('shopify', 'To Shopify'),
                                                ('odoo', 'From Shopify')],
                                     required=True, default='odoo')
    shopify_instance_id = fields.Many2one('shopify.configuration',
                                          string="Shopify Instance",
                                          required=True)
    draft = fields.Boolean('Draft Orders', default=False)
    type_order = fields.Selection(string='Type of order',
                                  selection=[('draft', 'Draft Orders'),
                                             ('confirmed', 'Confirmed Orders')],
                                  required=True, default='draft')
    def sync_orders(self):
        """ method to create queue job for exporting orders.It will also
            call the methods to create queue jobs for importing orders."""
        shopify_instance = self.shopify_instance_id
        if self.import_orders == 'shopify' and not self.shopify_instance_id.import_order:
            raise ValidationError('For Syncing Orders to Shopify Enable Export Orders option in shopify configuration ')
        else:
            if self.import_orders == 'shopify':
                sale_order = self.env['sale.order'].search(
                    [('state', '=', 'draft'),
                     ('company_id', 'in', [False, shopify_instance.company_id.id])])
                order_list = []
                size = 50
                for i in range(0, len(sale_order), size):
                    order_list.append(sale_order[i:i + size])
                for order in order_list:
                    delay = self.with_delay(priority=1, eta=60)
                    delay.export_orders_to_shopify(order)
            else:
                if self.type_order == 'draft':
                    self.sync_draft_orders()
                elif self.type_order == 'confirmed':
                    self.sync_confirmed_orders()

    def sync_confirmed_orders(self):
        """Method to create queue jobs for importing confirmed orders."""
        api_key = self.shopify_instance_id.con_endpoint
        password = self.shopify_instance_id.consumer_key
        store_name = self.shopify_instance_id.shop_name
        version = self.shopify_instance_id.version
        order_url = "https://%s:%s@%s/admin/api/%s/orders.json" % (
            api_key, password, store_name, version)
        payload = []
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("GET", order_url,
                                    headers=headers,
                                    data=payload)
        j = response.json()
        if 'orders' in j:
            shopify_orders = j['orders']
            delay = self.with_delay(priority=1, eta=60)
            delay.import_confirmed_orders_from_shopify(shopify_orders)
            _logger.info(
                '++++++++++confirmed orders++++++++++++++++++++',
                pprint.pformat(shopify_orders))

        order_link = response.headers[
            'link'] if 'link' in response.headers else ''
        order_links = order_link.split(',')
        for link in order_links:
            match = re.compile(r'rel=\"next\"').search(link)
            if match:
                order_link = link
        rel = re.search('rel=\"(.*)\"', order_link).group(
            1) if 'link' in response.headers else ''
        if order_link and rel == 'next':
            i = 0
            n = 1
            while i < n:
                page_info = re.search('page_info=(.*)>',
                                      order_link).group(1)
                limit = 50
                order_link = "https://%s:%s@%s/admin/api/%s/orders.json?limit=%s&page_info=%s" % (
                    api_key, password, store_name, version, limit,
                    page_info)
                response = requests.request('GET', order_link,
                                            headers=headers, data=payload)
                j = response.json()
                if 'orders' in j:
                    orders = j['orders']
                    delay = self.with_delay(priority=1, eta=60)
                    delay.import_confirmed_orders_from_shopify(orders)
                    _logger.info(
                        '++++++++++confirmed orders++++++++++++++++++++',
                        pprint.pformat(orders))

                order_link = response.headers['link']
                order_links = order_link.split(',')
                for link in order_links:
                    match = re.compile(r'rel=\"next\"').search(link)
                    if match:
                        order_link = link
                rel = re.search('rel=\"next\"', order_link)
                i += 1
                if order_link and rel is not None:
                    n += 1

    def sync_draft_orders(self):
        """Method to create queue jobs for importing draft orders."""
        api_key = self.shopify_instance_id.con_endpoint
        password = self.shopify_instance_id.consumer_key
        store_name = self.shopify_instance_id.shop_name
        version = self.shopify_instance_id.version
        order_url = "https://%s:%s@%s/admin/api/%s/draft_orders.json" % (
            api_key, password, store_name, version)
        payload = []
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.request("GET", order_url,
                                    headers=headers,
                                    data=payload)
        j = response.json()
        if 'draft_orders' in j:
            shopify_orders = j['draft_orders']
            delay = self.with_delay(priority=1, eta=60)
            delay.import_draft_orders_from_shopify(shopify_orders)
            _logger.info(
                '++++++++++draft orders++++++++++++++++++++',
                pprint.pformat(shopify_orders))

        order_link = response.headers['link'] if 'link' in response.headers else ''
        order_links = order_link.split(',')
        for link in order_links:
            match = re.compile(r'rel=\"next\"').search(link)
            if match:
                order_link = link
        rel = re.search('rel=\"(.*)\"', order_link).group(
            1) if 'link' in response.headers else ''
        if order_link and rel == 'next':
            i = 0
            n = 1
            while i < n:
                page_info = re.search('page_info=(.*)>',
                                      order_link).group(1)
                limit = re.search('limit=(.*)&', order_link).group(1)
                order_link = "https://%s:%s@%s/admin/api/%s/draft_orders.json?limit=%s&page_info=%s" % (
                    api_key, password, store_name, version, limit,
                    page_info)
                response = requests.request('GET', order_link,
                                            headers=headers, data=payload)
                j = response.json()
                if 'draft_orders' in j:
                    orders = j['draft_orders']
                    delay = self.with_delay(priority=1, eta=60)
                    delay.import_draft_orders_from_shopify(orders)
                    _logger.info(
                        '++++++++++draft orders++++++++++++++++++++',
                        pprint.pformat(orders))

                order_link = response.headers['link']
                order_links = order_link.split(',')
                for link in order_links:
                    match = re.compile(r'rel=\"next\"').search(link)
                    if match:
                        order_link = link
                rel = re.search('rel=\"next\"', order_link)
                i += 1
                if order_link and rel is not None:
                    n += 1

    def import_confirmed_orders_from_shopify(self,shopify_orders):
        """ Method to import confirmed orders from shopify to odoo.
            Queue job evokes this method for creating confirmed orders in odoo.

            shopify_orders(list):list of dictionary with orders values.
        """
        vals = {}
        shopify_instance = self.shopify_instance_id
        api_key = self.shopify_instance_id.con_endpoint
        password = self.shopify_instance_id.consumer_key
        store_name = self.shopify_instance_id.shop_name
        version = self.shopify_instance_id.version
        _logger.info(
            '++++++++++importing confirmed orders from shopify++++++++++++++++++++',pprint.pformat(shopify_orders))
        for each in shopify_orders:
            shopify_id = each['id']
            existing_order = self.env['sale.order'].search(
                [('shopify_sync_ids.shopify_order_id', '=', shopify_id)])
            if not existing_order:
                if 'customer' in each.keys():
                    customer_id = each['customer'].get('id')
                    if each['customer']['first_name'] or each['customer']['last_name']:
                        partner_id = self.env['res.partner'].sudo().search(
                            [('shopify_sync_ids.shopify_customer_id', '=',
                              customer_id),
                             ('shopify_sync_ids.instance_id', '=',
                              shopify_instance.id),
                             ('company_id', 'in',
                              [shopify_instance.company_id.id, False])], limit=1).id
                        if not partner_id:
                            customer_url = "https://%s:%s@%s/admin/api/%s/customers/%s.json" % (
                                api_key, password, store_name, version, customer_id)
                            payload = []
                            headers = {
                                'Content-Type': 'application/json'
                            }
                            response = requests.request("GET", customer_url,
                                                        headers=headers,
                                                        data=payload)
                            customer_response = response.json()
                            customer_vals = {}
                            customer = customer_response['customer']
                            if customer['addresses']:
                                country_id = self.env['res.country'].sudo().search([
                                    ('name', '=', customer['addresses'][0]['country'])
                                ])
                                state_id = self.env['res.country.state'].sudo().search([
                                    ('name', '=', customer['addresses'][0]['province'])
                                ])
                                customer_vals = {
                                    'street': customer['addresses'][0]['address1'],
                                    'street2': customer['addresses'][0]['address2'],
                                    'city': customer['addresses'][0]['city'],
                                    'country_id': country_id.id if country_id else False,
                                    'state_id': state_id.id if state_id else False,
                                    'zip': customer['addresses'][0]['zip'],
                                }
                            if customer['first_name'] and not customer['last_name']:
                                customer_vals['name'] = customer['first_name']
                            if customer['last_name'] and not customer['first_name']:
                                customer_vals['name'] = customer['last_name']
                            if customer['first_name'] and customer['last_name']:
                                customer_vals['name'] = customer['first_name'] + ' ' + customer['last_name']
                            customer_vals['email'] = customer['email']
                            customer_vals['phone'] = customer['phone']
                            customer_vals['shopify_customer_id'] = customer['id']
                            customer_vals['shopify_instance_id'] = shopify_instance.id
                            customer_vals['synced_customer'] = True
                            customer_vals['company_id'] = shopify_instance.company_id.id
                            partner_id = self.env['res.partner'].sudo().create(customer_vals).id
                            partner_ = self.env['res.partner'].browse(partner_id)
                            partner_.shopify_sync_ids.sudo().create({
                                'instance_id': self.shopify_instance_id.id,
                                'shopify_customer_id': customer_id,
                                'customer_id': partner_id,
                            })
                        vals["partner_id"] = partner_id
                        if each['shipping_address']:
                            county_id = self.env['res.country'].search([
                                ('name', '=', each['shipping_address']['country'])
                            ])
                            state_id = self.env['res.country.state'].search([
                                ('name', '=', each['shipping_address']['province'])
                            ])
                            shipping_child_id = self.env['res.partner'].sudo().create({
                                "name": each['shipping_address']['first_name'] if each['shipping_address'][
                                    'first_name'] else '',
                                "street": each['shipping_address']['address1'] if each['shipping_address'][
                                    'address1'] else '',
                                "street2": each['shipping_address']['address2'] if each['shipping_address'][
                                    'address2'] else '',
                                "city": each['shipping_address']['city'] if each['shipping_address']['city'] else '',
                                "state_id": state_id.id or None,
                                "phone": each['shipping_address']['phone'] if each['shipping_address'][
                                    'phone'] else None,
                                "zip": each['shipping_address']['zip'] if each['shipping_address']['zip'] else '',
                                "country_id": county_id.id or None,
                                "parent_id": partner_id,
                                "type": 'delivery',
                            }).id
                            vals['partner_shipping_id'] = shipping_child_id
                        if each['billing_address']:
                            county_id = self.env['res.country'].search([
                                ('name', '=', each['shipping_address']['country'])
                            ])
                            state_id = self.env['res.country.state'].search([
                                ('name', '=', each['shipping_address']['province'])
                            ])
                            billing_child_id = self.env['res.partner'].sudo().create({
                                "name": each['billing_address']['first_name'] if each['billing_address'][
                                    'first_name'] else '',
                                "street": each['billing_address']['address1'] if each['billing_address'][
                                    'address1'] else '',
                                "street2": each['billing_address']['address2'] if each['billing_address'][
                                    'address2'] else '',
                                "city": each['billing_address']['city'] if each['billing_address']['city'] else '',
                                "state_id": state_id.id or None,
                                "phone": each['billing_address']['phone'] if each['billing_address'][
                                    'phone'] else None,
                                "zip": each['billing_address']['zip'] if each['billing_address']['zip'] else '',
                                "country_id": county_id.id or None,
                                "parent_id": partner_id,
                                "type": 'invoice'
                            }).id
                            vals['partner_invoice_id'] = billing_child_id

                    else:
                        self.env['log.message'].sudo().create({
                            'name': ' Creation of order : ' + each['name']+ ' is not processed. Customer does not have a name.',
                            'shopify_instance_id': self.shopify_instance_id.id,
                            'model': 'sale.order',
                        })
                        continue
                else:
                    self.env['log.message'].sudo().create({
                        'name': 'Creation order : ' + each['name']+' is not processed. Order does not contain a customer.',
                        'shopify_instance_id': self.shopify_instance_id.id,
                        'model': 'sale.order',
                    })
                    continue
                if each['tax_lines']:
                    tax = each['tax_lines'][0]['rate']
                    tax_group = each['tax_lines'][0]["title"]
                    taxes = tax * 100
                    tax_name = self.env[
                        'account.tax'].search(
                        [('amount', '=', taxes),
                         ('tax_group_id', '=', tax_group),
                         ('type_tax_use', '=', 'sale')])

                    if not tax_name:
                        tax_group_id = self.env['account.tax.group'].create(
                            {'name': tax_group})
                        tax_name = self.env['account.tax'].create(
                            {'name': tax_group + str(taxes) + '%',
                             'type_tax_use': 'sale',
                             'amount_type': 'percent',
                             'tax_group_id': tax_group_id.id,
                             'amount': taxes,
                             })
                else:
                    tax_name = None
                vals["date_order"] = str(odoo.fields.Datetime.to_string(
                    dateutil.parser.parse(each['created_at']).astimezone(
                        pytz.utc)))
                vals["shopify_order_id"] = each['id']
                vals["name"] = each['name']
                vals['shopify_instance_id'] = shopify_instance.id
                fulfillment_status = each['fulfillment_status']
                payment_status = each['financial_status']
                fulfillment = 'fulfilled' \
                    if fulfillment_status == 'fulfilled' \
                    else 'partially_fulfilled' \
                    if fulfillment_status == 'partially_fulfilled' \
                    else 'un_fulfilled'
                payment = 'paid' if payment_status == 'paid' \
                    else 'partially_paid' \
                    if payment_status == 'partially_paid' \
                    else 'partially_refunded' \
                    if payment_status == 'partially_refunded' \
                    else 'refunded' if payment_status == 'refunded' \
                    else 'unpaid'
                sale_order = self.env['sale.order']
                so = sale_order.create(vals)
                so.shopify_sync_ids.sudo().create({
                    'instance_id': self.shopify_instance_id.id,
                    'shopify_order_id': each['id'],
                    'shopify_order_name': each['name'],
                    'shopify_order_number': each['number'],
                    'fulfillment_status': fulfillment,
                    'payment_status': payment,
                    'order_id': so.id,
                    'synced_order': True,
                })
                so.shopify_order_id = each['id']
                currency = self.env['res.currency'].sudo().search(
                    [
                        ('name', 'ilike', each['currency']),
                        ('active', 'in', [False, True]),
                    ])
                if currency and not currency.active:
                    currency.sudo().write({
                        'active': True,
                    })
                line_vals_list = []
                for line in each['line_items']:
                    discount = 0.0
                    if line['discount_allocations']:
                        discount = line['discount_allocations'][0]['amount']
                    product_id = self.env['product.product'].sudo().search([('shopify_product_id', '=', line['product_id']), ('shopify_sync_ids.instance_id', '=', shopify_instance.id), ('company_id', 'in', [shopify_instance.company_id.id, False])])
                    if not product_id:
                        product = line['product_id']
                        product_response = self.env['product.wizard'].create_product_by_id(shopify_instance, api_key, password, store_name, version, product)
                        if 'errors' in product_response:
                            self.env['log.message'].sudo().create({
                                'name': ' Creation of product  order : ' + each['name'] + ' with product id:  ' + str(line['id']) + ' and name:  '+line['title']+'  is not processed. Product does not exists in Shopify.',
                                'shopify_instance_id': self.shopify_instance_id.id,
                                'model': 'sale.order',
                            })
                            continue
                        if line['variant_id']:
                            product_id = self.env['product.product'].search([
                                ('shopify_variant_id', '=', line['variant_id'])
                            ])
                    str_list = []
                    for desc_index in line['discount_allocations']:
                        discount_type = \
                            each['discount_applications'][
                                desc_index['discount_application_index']][
                                'type']
                        if discount_type == 'discount_code':
                            str_list.append(
                                each[
                                    'discount_applications'][
                                    desc_index[
                                        'discount_application_index']][
                                    'code'])
                        else:
                            str_list.append(
                                each[
                                    'discount_applications'][
                                    desc_index[
                                        'discount_application_index']][
                                    'title'])
                    line_vals = {
                        'product_id': product_id.id,
                        'price_unit': line['price'],
                        'product_uom_qty': line['quantity'],
                        'currency_id': currency.id,
                        'discount': (float(discount) / float(
                            line['price']) * 100) / float(line['quantity'])
                        if discount else 0,
                        'tax_id': [
                            (6, 0, tax_name.ids)] if tax_name else False,
                        'shopify_line_id': line['id'],
                        'shopify_instance_id': shopify_instance.id,
                        'shopify_taxable': line['taxable'],
                        'shopify_tax_amount': float(
                            line['tax_lines'][0]['price']) if
                        line['tax_lines'] else 0.0,
                        'shopify_discount_amount':
                            sum(float(i['amount']) for
                                i in line['discount_allocations']) if line[
                                'discount_allocations'] else 0.0,
                        'shopify_line_item_discount':
                            sum(float(
                                each[
                                    'discount_applications'][
                                    i['discount_application_index']][
                                    'value']) for i in
                                line['discount_allocations']) if
                            each[
                                'discount_applications'] else 0.0,
                        'shopify_discount_code': ','.join(str_list),
                        'order_id': so.id,
                        'company_id': shopify_instance.company_id.id,
                    }
                    if 'refunds' in each.keys():
                        for refunds in each['refunds']:
                            for refund_line in refunds['refund_line_items']:
                                if refund_line['line_item_id'] == line['id']:
                                    line_vals['product_uom_qty'] -= \
                                        refund_line['quantity']
                    line_vals_list.append(line_vals)
                if each['shipping_lines']:
                    shipping_lines = each['shipping_lines']
                    product_id = self.env.ref(
                        'shopify_odoo_connector.product_shopify_shipping_cost')
                    for line in shipping_lines:
                        shipping_line_vals = {
                            'product_id': product_id.id,
                            'name': line['title'] if line[
                                'title'] else product_id.name,
                            'price_unit': line['price'],
                            'product_uom_qty': 1,
                            'shopify_line_id': line['id'],
                            'tax_id': False,
                            'order_id': so.id,
                            'shopify_instance_id': shopify_instance.id,
                            'company_id': shopify_instance.company_id.id,
                        }
                        line_vals_list.append(shipping_line_vals)
                if float(each['current_total_discounts']) != 0.00:
                    discount_lines = each['current_total_discounts_set']
                    product_id = self.env.ref(
                        'shopify_odoo_connector.product_shopify_order_discount')
                    dicount_dict = {
                        'product_id': product_id.id,
                        'price_unit': -float(discount_lines['shop_money']['amount']),
                        'product_uom_qty': 1,
                        'tax_id': None,
                        'order_id': so.id,
                    }
                    line_vals_list.append(dicount_dict)
                sale_order_line = self.env['sale.order.line']
                sale_order_line.create(line_vals_list)
                if not self.draft:
                    so.action_confirm()

    def import_draft_orders_from_shopify(self, shopify_orders):
        """ Method to import draft orders from shopify to odoo.
            Queue job evokes this method for creating draft orders in odoo.

            shopify_orders(list):list of dictionary with order values
        """
        shopify_instance = self.shopify_instance_id
        api_key = self.shopify_instance_id.con_endpoint
        password = self.shopify_instance_id.consumer_key
        store_name = self.shopify_instance_id.shop_name
        version = self.shopify_instance_id.version
        vals = {}
        _logger.info(
            '++++++++++importing draft orders from shopify++++++++++++++++++++',
            pprint.pformat(shopify_orders))
        for each in shopify_orders:
            shopify_id = each['id']
            existing_order = self.env['sale.order'].search(
                [('shopify_sync_ids.shopify_order_id', '=', shopify_id)])
            if not existing_order and each['status'] != 'completed':
                if 'customer' in each.keys() and each['customer'] is not None:
                    if each['customer']['first_name'] or each['customer']['last_name']:
                        customer_id = each['customer'].get('id')
                        partner_id = self.env['res.partner'].sudo().search(
                            [('shopify_sync_ids.shopify_customer_id', '=',
                              customer_id),
                             ('shopify_sync_ids.instance_id', '=',
                              shopify_instance.id),
                             ('company_id', 'in',
                              [shopify_instance.company_id.id, False])],
                            limit=1).id
                        if not partner_id:
                            customer_url = "https://%s:%s@%s/admin/api/%s/customers/%s.json" % (
                                api_key, password, store_name, version,
                                customer_id)
                            payload = []
                            headers = {
                                'Content-Type': 'application/json'
                            }
                            response = requests.request("GET", customer_url,
                                                        headers=headers,
                                                        data=payload)
                            customer_response = response.json()

                            customer_vals = {}
                            customer = customer_response['customer']
                            if customer['addresses']:
                                country_id = self.env[
                                    'res.country'].sudo().search([
                                        ('name', '=',
                                         customer['addresses'][0]['country'])
                                    ])
                                state_id = self.env[
                                    'res.country.state'].sudo().search([
                                        ('name', '=',
                                         customer['addresses'][0]['province'])
                                    ])
                                customer_vals = {
                                    'street': customer['addresses'][0][
                                        'address1'],
                                    'street2': customer['addresses'][0][
                                        'address2'],
                                    'city': customer['addresses'][0]['city'],
                                    'country_id': country_id.id if country_id else False,
                                    'state_id': state_id.id if state_id else False,
                                    'zip': customer['addresses'][0]['zip'],
                                }
                            if customer['first_name'] and not customer['last_name']:
                                customer_vals['name'] = customer['first_name']
                            if customer['last_name'] and not customer['first_name']:
                                customer_vals['name'] = customer['last_name']
                            if customer['first_name'] and customer['last_name']:
                                customer_vals['name'] = customer['first_name'] + ' ' + customer['last_name']
                            customer_vals['email'] = customer['email']
                            customer_vals['phone'] = customer['phone']
                            customer_vals['shopify_customer_id'] = customer['id']
                            customer_vals['shopify_instance_id'] = shopify_instance.id
                            customer_vals['synced_customer'] = True
                            customer_vals['company_id'] = shopify_instance.company_id.id
                            partner_id = self.env['res.partner'].sudo().create(
                                customer_vals).id
                            partner_ = self.env['res.partner'].browse(
                                partner_id)
                            partner_.shopify_sync_ids.sudo().create({
                                'instance_id': self.shopify_instance_id.id,
                                'shopify_customer_id': customer_id,
                                'customer_id': partner_id,
                            })
                        vals["partner_id"] = partner_id

                        if each['shipping_address']:
                            county_id = self.env['res.country'].search([
                                ('name', '=',
                                 each['shipping_address']['country'])
                            ])
                            state_id = self.env['res.country.state'].search([
                                ('name', '=',
                                 each['shipping_address']['province'])
                            ])
                            shipping_child_id = self.env[
                                'res.partner'].sudo().create({
                                    "name": each['shipping_address'][
                                        'first_name'] if each['shipping_address'][
                                        'first_name'] else '',
                                    "street": each['shipping_address'][
                                        'address1'] if each['shipping_address'][
                                        'address1'] else '',
                                    "street2": each['shipping_address'][
                                        'address2'] if each['shipping_address'][
                                        'address2'] else '',
                                    "city": each['shipping_address']['city'] if
                                    each['shipping_address']['city'] else '',
                                    "state_id": state_id.id or None,
                                    "phone": each['shipping_address']['phone'] if
                                    each['shipping_address'][
                                        'phone'] else None,
                                    "zip": each['shipping_address']['zip'] if
                                    each['shipping_address']['zip'] else '',
                                    "country_id": county_id.id or None,
                                    "parent_id": partner_id,
                                    "type": 'delivery',
                                }).id
                            vals['partner_shipping_id'] = shipping_child_id
                        if each['billing_address']:
                            county_id = self.env['res.country'].search([
                                ('name', '=',
                                 each['shipping_address']['country'])
                            ])
                            state_id = self.env['res.country.state'].search([
                                ('name', '=',
                                 each['shipping_address']['province'])
                            ])
                            billing_child_id = self.env[
                                'res.partner'].sudo().create({
                                    "name": each['billing_address'][
                                        'first_name'] if each['billing_address'][
                                        'first_name'] else '',
                                    "street": each['billing_address'][
                                        'address1'] if each['billing_address'][
                                        'address1'] else '',
                                    "street2": each['billing_address'][
                                        'address2'] if each['billing_address'][
                                        'address2'] else '',
                                    "city": each['billing_address']['city'] if
                                    each['billing_address']['city'] else '',
                                    "state_id": state_id.id or None,
                                    "phone": each['billing_address']['phone'] if
                                    each['billing_address'][
                                        'phone'] else None,
                                    "zip": each['billing_address']['zip'] if
                                    each['billing_address']['zip'] else '',
                                    "country_id": county_id.id or None,
                                    "parent_id": partner_id,
                                    "type": 'invoice'
                                }).id
                            vals['partner_invoice_id'] = billing_child_id
                    else:
                        self.env['log.message'].sudo().create({
                            'name': ' Creation of draft order : ' + each[
                                'name'] + ' is not processed. Customer does not have a name.',
                            'shopify_instance_id': self.shopify_instance_id.id,
                            'model': 'sale.order',
                        })
                        continue
                else:
                    self.env['log.message'].sudo().create({
                        'name': 'Creation draft order : ' + each[
                            'name'] + ' is not processed. Order does not contain a customer.',
                        'shopify_instance_id': self.shopify_instance_id.id,
                        'model': 'sale.order',
                    })
                    continue
                if each['tax_lines']:
                    tax = each['tax_lines'][0]['rate']
                    tax_group = each['tax_lines'][0]["title"]
                    taxes = tax * 100
                    tax_name = self.env[
                        'account.tax'].search(
                        [('amount', '=', taxes),
                         ('tax_group_id', '=', tax_group),
                         ('type_tax_use', '=', 'sale')])

                    if not tax_name:
                        tax_group_id = self.env['account.tax.group'].create(
                            {'name': tax_group})
                        tax_name = self.env['account.tax'].create(
                            {'name': tax_group + str(taxes) + '%',
                             'type_tax_use': 'sale',
                             'amount_type': 'percent',
                             'tax_group_id': tax_group_id.id,
                             'amount': taxes,
                             })
                else:
                    tax_name = None
                vals["date_order"] = str(odoo.fields.Datetime.to_string(
                    dateutil.parser.parse(each['created_at']).astimezone(
                        pytz.utc)))
                vals["shopify_order_id"] = each['id']
                vals["name"] = each['name']
                vals['shopify_instance_id'] = shopify_instance.id
                sale_order = self.env['sale.order']
                so = sale_order.create(vals)

                so.shopify_sync_ids.sudo().create({
                    'instance_id': self.shopify_instance_id.id,
                    'shopify_order_id': each['id'],
                    'shopify_order_name': each['name'],
                    'shopify_order_number': each['id'],
                    'order_status': each['status'],
                    'order_id': so.id,
                    'synced_order': True,
                })
                so.shopify_order_id = each['id']

                currency = self.env['res.currency'].sudo().search(
                    [
                        ('name', 'ilike', each['currency']),
                        ('active', 'in', [False, True]),
                    ])
                if currency and not currency.active:
                    currency.sudo().write({
                        'active': True,
                    })
                line_vals_list = []
                for line in each['line_items']:
                    discount = 0.0
                    if line['applied_discount']:
                        discount = line['applied_discount']['amount']
                    product_shopify_id = line['product_id']
                    product_name = line['title']
                    product_id = self.env['product.product'].sudo().search(
                        [('shopify_product_id', '=',
                          line['product_id']), (
                         'shopify_sync_ids.instance_id', '=',
                         shopify_instance.id),
                         ('company_id', 'in',
                          [shopify_instance.company_id.id, False])])

                    if not product_id:
                        product = line['product_id']
                        product_response = self.env[
                            'product.wizard'].create_product_by_id(
                            shopify_instance, api_key, password, store_name,
                            version, product)
                        if 'errors' in product_response:
                            self.env['log.message'].sudo().create({
                                'name': ' Creation of product  order : ' +
                                        each[
                                            'name'] + ' with product id:  ' + str(line['id']) + ' and name:  ' + line['title'] + '  is not processed. Product does not exists in Shopify.',
                                'shopify_instance_id': self.shopify_instance_id.id,
                                'model': 'sale.order',
                            })
                            continue
                        if line['variant_id']:
                            product_id = self.env['product.product'].search([
                                ('shopify_variant_id', '=', line['variant_id'])
                            ])

                    str_list = []
                    line_vals = {
                        'product_id': product_id.id,
                        'price_unit': line['price'],
                        'name': ' ',
                        'product_uom_qty': line['quantity'],
                        'currency_id': currency.id,
                        'discount': (float(discount) / float(
                            line['price']) * 100) / float(line['quantity'])
                        if discount else 0,
                        'tax_id': [
                            (6, 0, tax_name.ids)] if tax_name else False,
                        'shopify_line_id': line['id'],
                        'shopify_instance_id': shopify_instance.id,
                        'shopify_taxable': line['taxable'],
                        'shopify_tax_amount': float(
                            line['tax_lines'][0]['price']) if
                        line['tax_lines'] else 0.0,
                        'shopify_discount_amount': float(
                            line['applied_discount']['amount']) if line[
                            'applied_discount'] else 0.0,
                        'shopify_line_item_discount': float(
                            line['applied_discount']['amount']) if line[
                            'applied_discount'] else 0.0,
                        'shopify_discount_code': ','.join(str_list),
                        'order_id': so.id,
                        'company_id': shopify_instance.company_id.id,
                    }
                    if 'refunds' in each.keys():
                        for refunds in each['refunds']:
                            for refund_line in refunds['refund_line_items']:
                                if refund_line['line_item_id'] == line['id']:
                                    line_vals['product_uom_qty'] -= \
                                        refund_line['quantity']
                    line_vals_list.append(line_vals)
                if each['shipping_line']:
                    shipping_line = each['shipping_line']
                    shipping_product_id = self.env.ref(
                        'shopify_odoo_connector.product_shopify_shipping_cost')
                    line_vals = {
                        'product_id': shipping_product_id.id,
                        'name': shipping_line['title'] if shipping_line[
                            'title'] else shipping_product_id.name,
                        'price_unit': shipping_line['price'],
                        'product_uom_qty': 1,
                        'shopify_line_id': '',
                        'tax_id': False,
                        'order_id': so.id,
                        'shopify_instance_id': shopify_instance.id,
                        'company_id': shopify_instance.company_id.id,
                    }
                    line_vals_list.append(line_vals)
                if each['applied_discount']:
                    discount_line = each['applied_discount']
                    discount_product_id = self.env.ref(
                        'shopify_odoo_connector.product_shopify_order_discount')
                    dis_line_vals = {
                        'product_id': discount_product_id.id,
                        'name': discount_line['title'] if discount_line[
                            'title'] else discount_product_id.name + " : " + discount_line['value_type'] + " - " + discount_line['value'],
                        'price_unit': -float(discount_line['amount']),
                        'order_id': so.id,
                        'tax_id': None,
                    }
                    line_vals_list.append(dis_line_vals)
                sale_order_line = self.env['sale.order.line']
                sale_order_line.create(line_vals_list)

    def export_orders_to_shopify(self, sale_order):
        """ Method to export orders from odoo to shopify.
            Queue job evokes this method to export odoo orders.

            sale_order(list):list of dictionary with order values.
        """
        api_key = self.shopify_instance_id.con_endpoint
        password = self.shopify_instance_id.consumer_key
        store_name = self.shopify_instance_id.shop_name
        version = self.shopify_instance_id.version
        _logger.info(
            '++++++++++exporting orders to shopify++++++++++++++++++++',
            pprint.pformat(sale_order))
        order_url = "https://%s:%s@%s/admin/api/%s/draft_orders.json" % (
            api_key, password, store_name, version)
        for order in sale_order:
            instance_ids = order.shopify_sync_ids.mapped(
                'instance_id.id')
            if self.shopify_instance_id.id not in instance_ids:
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
                if response.status_code == 201:
                    response_rec = response.json()
                    response_order_id = response_rec['draft_order']['id']
                    response_status = response_rec['draft_order']['status']
                    response_name = response_rec['draft_order']['name']
                    order.shopify_sync_ids.sudo().create({
                        'instance_id': self.shopify_instance_id.id,
                        'shopify_order_id': response_order_id,
                        'shopify_order_name': response_name,
                        'shopify_order_number': response_order_id,
                        'order_status': response_status,
                        'order_id': order.id,
                        'synced_order': True,
                    })
                    order.shopify_order_id = response_order_id
