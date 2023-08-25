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

from odoo import models, fields
import requests


class GiftCards(models.TransientModel):
    _name = 'gift.cards'
    _description = 'Gift Cards'

    shopify_instance_id = fields.Many2one('shopify.configuration',
                                          string="Shopify Instance",
                                          required=True)

    def sync_gift_cards(self):
        api_key = self.shopify_instance_id.con_endpoint
        password = self.shopify_instance_id.consumer_key
        store_name = self.shopify_instance_id.shop_name
        version = self.shopify_instance_id.version
        gift_card_url = "https://%s:%s@%s/admin/api/%s/gift_cards.json" % (
            api_key, password, store_name, version)
        payload = []
        headers = {
            'Content-Type': 'application/json'
        }
        requests.request("GET", gift_card_url,
                         headers=headers, data=payload)
