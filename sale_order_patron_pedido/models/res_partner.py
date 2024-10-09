# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import logging
from itertools import *
from datetime import datetime, timedelta


class ResPartner(models.Model):
	_inherit = "res.partner"

	patron_pedido_line_ids = fields.One2many('patron.pedido.line','partner_id',
		string="Lista de Corridas")

	descripcion = fields.Char(string="Descripción General")
	show_tallas_medias = fields.Boolean(string="Mostrar Tallas Medias")