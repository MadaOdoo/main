# -*- coding: utf-8 -*-
# File:           madkting_config.py
# Author:         Gerardo Lopez
# Copyright:      (C) 2019 All rights reserved by Madkting
# Created:        2023-04-18

from odoo import models, fields


class MadktingConfig(models.Model):
    _inherit = 'madkting.config'
    _description = 'Config'

    validate_cafs = fields.Boolean('Valida folios facturacion')
    cafs_document_type_id = fields.Many2one('l10n_latam.document.type', 'Tipo de documento')
    validate_doctype_nit = fields.Boolean("Valida tipo de identificacion NIT")
