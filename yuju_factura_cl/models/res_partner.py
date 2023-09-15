# -*- coding: utf-8 -*-
# File:           madkting_config.py
# Author:         Gerardo Lopez
# Copyright:      (C) 2019 All rights reserved by Madkting
# Created:        2023-04-18

import requests

from odoo import models, fields, api
from odoo import exceptions
from datetime import datetime
from ..log.logger import logger
from ..responses import results

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def update_mapping_fields(self, customer_data):

        config = self.env['madkting.config'].get_config()
        
        doc_type = None
        if customer_data.get('doc_type') and config.validate_doctype_nit:
            doc_type = customer_data.get('doc_type')

            if doc_type == "NIT":
                cutomer_vat = customer_data.get("vat")

                if customer_vat and len(customer_vat) == 10 and customer_vat.find("-") < 0:
                    customer_vat = f"{customer_vat[:len(customer_vat) - 1]}-{cutomer_vat[-1]}"
                    customer_data["vat"] = customer_vat

        customer_data = super(ResPartner, self).update_mapping_fields(customer_data)
        return customer_data