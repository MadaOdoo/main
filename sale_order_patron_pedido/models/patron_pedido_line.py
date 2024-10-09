# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import logging
from itertools import *
from datetime import datetime, timedelta

class PatronPedidoLine(models.Model):
	_name = 'patron.pedido.line'
	_description = "Lista de Corridas"
	_rec_name = "name_corrida"


	partner_id = fields.Many2one('res.partner',string="Cliente",ondelete="cascade")
	sequence = fields.Integer(string="Sequence")
	name_corrida= fields.Char(string="Nombre Corrida")

	talla_21 = fields.Integer(string="21")
	talla_21_5 = fields.Integer(string="21.5")
	talla_22 = fields.Integer(string="22")
	talla_22_5 = fields.Integer(string="22.5")
	talla_23 = fields.Integer(string="23")
	talla_23_5 = fields.Integer(string="23.5")
	talla_24 = fields.Integer(string="24")
	talla_24_5 = fields.Integer(string="24.5")
	talla_25 = fields.Integer(string="25")
	talla_25_5 = fields.Integer(string="25.5")
	talla_26 = fields.Integer(string="26")
	talla_26_5 = fields.Integer(string="26.5")
	talla_27 = fields.Integer(string="27")
	talla_27_5 = fields.Integer(string="27.5")
	talla_28 = fields.Integer(string="28")

	total_pares = fields.Integer(string="Total",compute="compute_campo_total_pares",store=True)

	@api.depends(
		'talla_21',
		'talla_21_5',
		'talla_22',
		'talla_22_5',
		'talla_23',
		'talla_23_5',
		'talla_24',
		'talla_24_5',
		'talla_25',
		'talla_25_5',
		'talla_26',
		'talla_26_5',
		'talla_27',
		'talla_27_5',
		'talla_28')
	def compute_campo_total_pares(self):
		for rec in self:
			rec.total_pares = rec.talla_21 + rec.talla_21_5 + rec.talla_22 + rec.talla_22_5 + \
				rec.talla_23 + rec.talla_23_5 + rec.talla_24 + rec.talla_24_5 + rec.talla_25 + \
				rec.talla_25_5 + rec.talla_26 + rec.talla_26_5 + rec.talla_27 + rec.talla_27_5 + \
				rec.talla_28
