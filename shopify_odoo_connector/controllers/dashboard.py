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
from odoo import http
from odoo.http import request


class Dashboard(http.Controller):
    """Class for http controller.
        Methods:
            def dashboard(self, **kw):
                method fetch data from shopify.configuration model then it
                returns to js.
    """
    @http.route(['/dashboard'], type="json", auth="public")
    def dashboard(self, **kw):
        """
            method fetch data from shopify.configuration model then it return 
            to js. 

            kw(dict):empty dictionary

            dict: returns a dictionary with id,instance,order,customer & 
            product details of shopify instance.
        """
        instances = request.env['shopify.configuration'].search([])
        values = []
        for instance in instances:
            values.append({
                'id': instance.id,
                'instance': instance.name,
                'order': instance.order_count,
                'customer': instance.customer_count,
                'product': instance.product_count,
            })
        return values


class TotalDashboard(http.Controller):
    """Class for http controller.
        Methods:
            def dashboard(self, **kw):
                method to find count of total synced order, product and customer.
                Then passes the values to dashboard.
        """
    @http.route(['/total_dashboard'], type="json", auth="public")
    def total_dashboard(self, **kw):
        """
            method to find count of total synced order, product and customer.
            Then passes the values to dashboard.

            kw(dict):empty dictionary

            dict: returns total count of orders, products and customers as
            dictionary.
        """
        values = []
        customer = request.env['res.partner'].search_count(
            [('shopify_sync_ids', '!=', False)])
        product = request.env['product.template'].search_count(
            [('shopify_sync_ids', '!=', False)])
        order = request.env['sale.order'].search_count(
            [('shopify_sync_ids', '!=', False)])
        values.append({
            'order': order,
            'customer': customer,
            'product': product,
        })
        return values
