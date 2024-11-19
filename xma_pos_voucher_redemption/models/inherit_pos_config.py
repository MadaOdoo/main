# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import UserError
import requests

class InheritPosConfig(models.Model):
    _inherit = 'pos.config'

    token = fields.Char(
        string='Token API',
        readonly=True
    )
    apply_voucher = fields.Boolean(related="company_id.apply_voucher")


class InheritResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    token = fields.Char(
        related='pos_config_id.token',
        readonly=True
    )

    apply_voucher = fields.Boolean(
        string="Aplica vales",
        related='company_id.apply_voucher',
        store=True,
        readonly=False
    )

    def generateToken(self):
        url = 'https://api-dev.prestavale.mx/api/usuarios/login-prestavale'
        data = {
            'email': 'odoo@prestavale.mx',
            'password': '43214321'
        }
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                response_dict = response.json()
                self.pos_config_id.token = response_dict['id']
            elif response.status_code == 400:
                raise UserError(_('Error con uno o varios parámetros no válidos en la solicitud POST durante la autenticación. Por favor contacte a un administrador. (%s)', str(response)))
            elif response.status_code == 500:
                raise UserError(_('Debido a un problema técnico, la autenticación no pudo ser realizada.'))
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise UserError(_('No se puede conectar. Por favor contacte a un administrador. (%s)', e))
