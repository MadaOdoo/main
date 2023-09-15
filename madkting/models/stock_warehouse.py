# -*- coding: utf-8 -*-
# File:           stock_warehouse.py
# Author:         Gerardo Lopez Vega
# Copyright:      (C) 2021 All rights reserved by Madkting
# Created:        2021-06-09

from odoo import models, fields, api
from odoo import exceptions
from datetime import datetime
from ..log.logger import logger
from ..responses import results

class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    dropship_enabled = fields.Boolean("Habilitar Dropship")