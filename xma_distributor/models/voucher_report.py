from odoo import models, fields

class VoucherReport(models.Model):
    _name = "voucher.report"
    _description = "Reporte de Vales"

    is_vale = fields.Boolean(string="Es vale?")

    distribuidora_id = fields.Many2one(
        "res.partner",
        string="Distribuidora"
    )

    order_id = fields.Many2one(
        "pos.order",
        string="Pedido"
    )

    cantidad_pagos = fields.Integer(string="Cantidad de pagos")
    monto_seguro = fields.Float(string="Monto seguro")
    pago_quincenal = fields.Float(string="Pago quincenal")
    total_pago = fields.Float(string="Total de pago")
    fecha = fields.Date(string="Fecha")
    num_vale = fields.Char(
        string="Numero de vale",
        readonly=True,
    )