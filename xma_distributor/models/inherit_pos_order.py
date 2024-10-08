# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, timedelta, datetime
from odoo.exceptions import UserError, ValidationError

class InheritPosOrder(models.Model):
    _inherit = 'pos.order'

    calculation = fields.Float(
        string="Cálculo",
        compute="compute_calculation"
    )

    percentage = fields.Float(
        string="Porcentaje (%) para la distribuidora",
        compute="compute_por"
    )

    def compute_por(self):
        por = self.env["ir.config_parameter"].get_param("xma_distributor.percentage")
        for rec in self:
            rec.percentage = por
    
    def compute_calculation(self):
        for rec in self:
            rec.calculation = (rec.pago_quincenal) * (rec.cantidad_pagos) * (rec.percentage / 100)

    def crear_reporte_vales(self, vals):
        for rec in vals:

            if not rec["str_fechas_pagare"]:
                fechas = None
            elif rec["str_fechas_pagare"] == "":
                fechas = None
            else:
                fechas = rec["str_fechas_pagare"].split(",")

            for num in range(1, rec.cantidad_pagos + 1):
                date_pay = None
                if fechas:
                    if len(fechas) >= num:
                        date_pay =  datetime.strptime(fechas[num - 1], '%d/%m/%Y').date()
                    else:
                        date_pay = None
                val = {
                    'distribuidora_id': rec.distribuidora_id.id,
                    'num_vale': rec.folio_vale, 
                    'order_id': rec.id, 
                    'cantidad_pagos': num, 
                    'monto_seguro': rec.monto_seguro, 
                    'pago_quincenal': rec.pago_quincenal, 
                    'total_pago': rec.total, 
                    'fecha': date_pay #+ quince
                }
                self.env['voucher.report'].create(val)
    
    @api.model
    def create(self, vals):
        rec = super(InheritPosOrder, self).create(vals)
        self.crear_reporte_vales(rec)
        return rec
