# -*- coding: utf-8 -*-

from odoo import models, fields

class InheritResConfigSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    percentage = fields.Float(
        string="Porcentaje (%) para aseguradora",
        config_parameter="xma_distributor.percentage"
    )