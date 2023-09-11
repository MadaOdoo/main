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
from odoo import fields, models


class ShopifySync(models.Model):
    """Class for the model shopify.sync."""
    _name = 'shopify.sync'
    _description = 'Shopify Sync'

    product_id = fields.Many2one('product.template',
                                 help='Id of the product in product template')
    product_prod_id = fields.Many2one('product.product',
                                      help='Id of the product in product product')
    customer_id = fields.Many2one('res.partner', help='Id of the customer')
    order_id = fields.Many2one('sale.order', help='Id of the order')
    instance_id = fields.Many2one('shopify.configuration',
                                  string="Instance", help='Id of instance')
    shopify_product_id = fields.Char('Product Id',
                                     help='Id of product in shopify')
    shopify_customer_id = fields.Char('Customer Id',
                                      help='Id of customer in shopify')
    shopify_order_id = fields.Char('Order Id', help='Id of order in shopify')
    synced_order = fields.Boolean(readonly=True, store=True,
                                  help='Will be true for synced orders')
    shopify_order_name = fields.Char('Name', readonly=True,
                                     store=True, help='Order name in shopify')
    shopify_order_number = fields.Char('Order No', readonly=True,
                                       store=True,
                                       help='Order number in shopify')
    payment_status = fields.Selection([('paid', 'Paid'),
                                       ('partially_paid', 'Partially Paid'),
                                       ('unpaid', 'Unpaid'),
                                       ('refunded', 'Refunded'),
                                       ('partially_refunded',
                                        'Partially Refunded')],
                                      string='Payment Status',
                                      default='unpaid', readonly=True,
                                      store=True, help='Order payment status')
    fulfillment_status = fields.Selection([('fulfilled', 'Fulfilled'),
                                           ('partially_fulfilled',
                                            'Partially Fulfiled'),
                                           ('un_fulfilled', 'Un Fulfilled')],
                                          string='Fulfillment Status',
                                          default='un_fulfilled',
                                          readonly=True, store=True,
                                          help='order fulfillment status')
    order_status = fields.Selection([('open', 'Open'),
                                     ('completed', 'Completed')],
                                    string='Order Status',
                                    default='open', readonly=True,
                                    store=True, help='Status of the order')
    last_order_id = fields.Char('Last order id', readonly=True,
                                store=True, help='Last order id')
