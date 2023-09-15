# -*- coding: utf-8 -*-
# File:           res_partner.py
# Author:         Israel Calderón
# Copyright:      (C) 2019 All rights reserved by Madkting
# Created:        2019-08-01

from odoo import models, api, fields
from urllib import parse
from ..responses import results
from ..log.logger import logger


class MadktingConfig(models.Model):
    _inherit = 'madkting.config'
    _description = 'Config'

    mrp_route = fields.Many2one('stock.route', string='Ruta para Fabricacion')
    delete_old_bom = fields.Boolean('Eliminar Ldm anterior')
    search_kit_by_sku = fields.Boolean('Buscar componente por SKU', default=True)
    update_product_type_kits = fields.Boolean('Modificar tipo de producto para combos', default=True)
    product_type_for_kits = fields.Selection(
        [('consu', 'Consumible'), ('product', 'Almacenable')], 
        string='Tipo de producto para combos', default='consu')