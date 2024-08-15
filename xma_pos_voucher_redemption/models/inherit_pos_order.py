# -*- coding: utf-8 -*-
import requests

from .amount_to_text import get_amount_to_text
from odoo import models, fields, api


class InheritPosOrder(models.Model):
    _inherit = 'pos.order'

    folio_vale = fields.Char(
        string="Folio del vale",
        readonly=True,
    )
    state_vale = fields.Char(
        string='Estado de vale',
        readonly=True,
    )
    is_vale = fields.Boolean(
        string='Es de vale',
        readonly=True,
    )
    distribuidora_id = fields.Many2one(
        'res.partner',
        string='Distribuidora',
        readonly=False,
    )
    cantidad_pagos = fields.Integer(
        string='Cantidad de pagos',
        readonly=True,
    )
    monto_seguro = fields.Float(
        string='Monto seguro',
        readonly=True,
    )
    pago_quincenal = fields.Float(
        string='Pago quincenal',
        readonly=True,
    )
    total = fields.Float(
        string='Total de pago',
        readonly=True,
    )
    fecha = fields.Date(
        string='Fecha de inicio de pago',
        readonly=True,
    )
    str_fechas_pagare = fields.Char(
        string='Fechas de pagare',
        readonly=True,
    )
    porcentaje_comision = fields.Float(
        string='Porcentaje de comision',
        readonly=True,
    )
    monto_seguro_por_quincena = fields.Float(
        string='Monto seguro por quincena',
        readonly=True,
    )
    nombre_cliente = fields.Char(
        string='Nombre del cliente',
        readonly=True,
    )
    cliente_telefono = fields.Char(
        string='Telefono del cliente',
        related='partner_id.phone',
    )
    ife = fields.Char(
        string='IFE',
        related='partner_id.curp',
    )
    nombre_distribuidora = fields.Char(
        string='Nombre de la distribuidora',
        readonly=True,
    )

    @api.model
    def validar_vale(self, folio, pos_session_id, client_id, token):
        obj = {}
        try:
            afiliadoId = 2
            url = 'https://api-dev-dot-mada-dev.ue.r.appspot.com/api/creditosAfiliado/consultarPorFolio/?folio=%s&afiliadoId=%s&access_token=%s' % (folio,afiliadoId,token)
            response = requests.get(url)
            status_code = response.status_code
            res = response.json()
            # res = {'id': 31, 'cantidadPagos': 4, 'clienteId': None, 'folio': '00004', 'monto': None,
            #              'pagoQuincenal': None, 'estatus': 'porcobrar', 'distribuidoraId': 3,
            #              'createdAt': '2021-11-09T21:06:12.000Z', 'updatedAt': '2021-11-09T21:06:12.000Z',
            #              'number': 9,
            #              'fechaCanje': None, 'usuarioId': None, 'afiliadoId': None, 'tipo': 'fisico',
            #              'corteEjecutivoId': None,
            #              'nombreDistribuidora': 'Gisella  Castro  Corrales', 'curp': '123456', 'nombreCliente': 'Juan Perez',
            #              'limiteDistribuidora': 10000, 'prospectoId': 4,
            #              'firma': 'https://storage.googleapis.com/dev-prestavale-protected/b298b4d6cbe89-FD4.JPG?GoogleAccessId=storage-prestavale%40mada-dev.iam.gserviceaccount.com&Expires=1686946659&Signature=Dk0Sk6sFYEXHlNWJNVg0e46yNJK2pEp5I9CnmTeXcAsXja8CtgCEG9XvYyvqa%2BuStGzrPzzxE9vD4cwA6PR63mhB0HAs0YRCLCWivMZjAFBON8LdLjVwWLSE%2FdejK6OwE7gVFR6ja5%2F32AW3rMqnDDfXapGpwninbZUdgv6FnHXW%2BXpdPD1xlG0TxovvPd27C3E8acq1790H6tihHHkB72wZM6IoB5k2e%2FgLcImEl%2BQ7cGn3AiwYigwTTmBUo7JY3Mgw33bZ95ZPFwfCkTxDGz8kbSBJ7vm%2B%2B5kklZuzT5PO2LCuHYDlrtXriNjWOLRMb9kk6egNkBRYSYH%2Faa4jcQ%3D%3D'}
            if status_code == 200:
                if res.get('id'):
                    id_ = res.get('id') or 0
                    monto = res.get('monto') or 0
                    distribuidoraId = res.get('distribuidoraId') or 0
                    nombreDistribuidora = res.get('nombreDistribuidora') or 'Sin nombre de distribuidora'
                    estatus = res.get('estatus') or ''
                    limiteDistribuidora = res.get('limiteDistribuidora') or 0
                    firma = res.get('firma') or ''
                    nombreCliente = res.get('nombreCliente') or ''
                    ife = res.get('curp') or ''
                    pos_session = self.env['pos.session'].search([('id', '=', pos_session_id)])
                    ciudad = pos_session.config_id.warehouse_id.company_id.city or ''
                    client = self.env['res.partner'].search([('id', '=', client_id)])
                    telefono = client.phone or client.mobile or ''

                    obj['id'] = id_
                    obj['folio'] = folio
                    obj['monto'] = monto
                    obj['distribuidoraId'] = distribuidoraId
                    obj['nombreDistribuidora'] = nombreDistribuidora
                    obj['estatus'] = estatus
                    obj['limiteDistribuidora'] = limiteDistribuidora
                    obj['firma'] = firma
                    obj['nombre_cliente'] = nombreCliente
                    obj['ife'] = ife
                    obj['ciudad'] = ciudad
                    obj['cliente_telefono'] = telefono

                    pos_order = self.search_count([('folio_vale', '=', str(folio))])
                    if pos_order:
                        obj = {'nombreDistribuidora': nombreDistribuidora, 'folio': folio, 'estatus': 'canjeado'}
                    elif estatus != 'porcobrar':
                        obj = {'nombreDistribuidora': nombreDistribuidora, 'folio': folio, 'estatus': estatus}
                    else:
                        monto_con_dos_decimales = round(float(monto), 2)
                        limite_monto_con_dos_decimales = round(float(limiteDistribuidora), 2)
                        if monto_con_dos_decimales > 0 or limite_monto_con_dos_decimales > 0:
                            model_cajeo_vales = self.env['cajeo.vales'].search([('name','=',str(folio))],limit=1)
                            if model_cajeo_vales:
                                obj = {'nombreDistribuidora': nombreDistribuidora, 'folio': folio,
                                       'estatus': 'canjeado'}
            else:
                obj = res.get('error','')
        except Exception as e:
            obj = 'error: ' + str(e)
        return obj

    @api.model
    def limpiar_registro_vale(self, folio_de_vale=''):
        model_cajeo_vales = self.env['cajeo.vales'].search([('name','=',str(folio_de_vale))], limit=1)
        if model_cajeo_vales:
            model_cajeo_vales.unlink()
        return True

    @api.model
    def save_model_cajeo_vales(self, distribuidora_id=None, folio_de_vales=''):
        if distribuidora_id and folio_de_vales:
            model_cajeo_vales = self.env['cajeo.vales'].search([('name','=',folio_de_vales)],limit=1)
            if len(model_cajeo_vales) == 0:
                self.env['cajeo.vales'].create({
                    'name': str(folio_de_vales),
                })

    @api.model
    def get_opciones_de_pago(self, distribuidora_id, monto):
        obj = {}
        url = 'https://api-dev-dot-mada-dev.ue.r.appspot.com/api/creditosAfiliado/consultaConfiguracion'
        dato = {
            "distribuidoraId": distribuidora_id,
            "afiliado": "MADA",
            "montoVenta": monto
        }
        try:
            response = requests.post(url, json=dato)
            status_code = response.status_code
            res = response.json()
            # res = [{'cantidadPagos': 4, 'configId': 1, 'montoSeguro': 5,
            #                   'pagoQuincenal': '2.50', 'total': '7.50', 'fecha': '2023-06-30',
            #                   'opcion': '4 quincenas de $7.50, comenzando a pagar 2023-06-30'}]
            if status_code == 200:
                if len(res):
                    obj['status_code'] = status_code
                    obj['lista'] = res
                    obj['monto_total'] = monto
                    obj['monto_as_text'] = get_amount_to_text(int(monto), currency='MXN')
            else:
                obj['status_code'] = status_code
                obj['message'] = res.get('message','')
        except Exception as e:
            obj = 'error: ' + str(e)
        return obj

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super()._order_fields(ui_order)
        order_fields['is_vale'] = ui_order.get('is_vale','')
        order_fields['folio_vale'] = ui_order.get('folio_de_vale','')
        order_fields['state_vale'] = ui_order.get('state_de_vale','')
        order_fields['cantidad_pagos'] = ui_order.get('cantidad_pagos',0)
        order_fields['monto_seguro'] = ui_order.get('monto_seguro',0)
        order_fields['pago_quincenal'] = ui_order.get('pago_quincenal',0)
        order_fields['total'] = ui_order.get('total',0)
        order_fields['fecha'] = ui_order.get('fecha','')
        order_fields['str_fechas_pagare'] = ui_order.get('str_fechas','')
        order_fields['cliente_telefono'] = ui_order.get('cliente_telefono','')
        order_fields['porcentaje_comision'] = ui_order.get('porcentaje_comision','')
        order_fields['monto_seguro_por_quincena'] = ui_order.get('monto_seguro_por_quincena','')

        distribuidora_id = self.env['res.partner'].search(
            [('company_registry','=',ui_order.get('distribuidora_id','') or '')],
        ) or 0
        if distribuidora_id:
            order_fields['distribuidora_id'] = distribuidora_id.id
        return order_fields

    def _export_for_ui(self, order):
        result = super()._export_for_ui(order)
        result.update({
            'cantidad_pagos': order.cantidad_pagos,
            'pago_quincenal': order.pago_quincenal,
            'monto_seguro': order.monto_seguro,
            'total': order.total,
            'nombre_cliente': order.nombre_cliente,
            'cliente_telefono': order.cliente_telefono,
            'ife': order.ife,
        })
        return result

    @api.model
    def validar_canje_credito(self, dato, token):
        obj = {}
        url = 'https://api-dev-dot-mada-dev.ue.r.appspot.com/api/creditosAfiliado/canje-credito-mada?access_token=%s' % (token)
        self.nombre_cliente = f"{'nombres' in dato and dato['nombres'] or 'nombres'} {'primerApellido' in dato and dato['primerApellido'] or ''} {'segundoApellido' in dato and dato['segundoApellido'] or ''}"
        self.nombre_distribuidora = self.distribuidora_id.name
        try:
            response = requests.post(url, json=dato)
            status_code = response.status_code
            res = response.json()
            # res = {'pagare': {'infoPagos':
            #                         ['$2.50 + $5.00 (Plan de protección) = $7.50 al 30/06/2023.',
            #                         '$2.50 + $5.00 (Plan de protección) = $7.50 al 15/07/2023.',
            #                         '$2.50 + $5.00 (Plan de protección) = $7.50 al 31/07/2023.',
            #                         '$2.50 + $5.00 (Plan de protección) = $7.50 al 15/08/2023.'],
            #                     'fechasPago': ['30/06/2023', '15/07/2023', '31/07/2023', '15/08/2023'],
            #                     'leyenda': 'Plan de protección', 'folioDistribuidora': '00004',
            #                     'nombreDistribuidora': 'Gisella  Castro  Corrales'}}
            if status_code == 200:
                obj['status_code'] = status_code
                obj['fechasPago'] = res['pagare']['fechasPago']
                obj['respuesta_canje_credito'] = res
                obj['porcentaje_comision'] = res.get('porcentajeComision', 0)
                obj['monto_seguro_por_quincena'] = res.get('montoSeguroPorQuincena', 0)
            else:
                obj['status_code'] = status_code
                obj['message'] = res.get('message','')
        except Exception as e:
            obj = 'error: ' + str(e)
        return obj

# x: Usado

# A-00001-0004 x
# A-00001-0001 x
# A-00001-0003 x
# A-00001-0006 x
# A-00001-0007 x
# A-00001-0008 x
# A-00001-0009 x
# A-00001-0010 x
# A-00001-0005
# A-00003-0002
# A-00003-0004
# A-00003-0003
# A-00003-0007
# A-00003-0006
# A-00003-0005
# A-00003-0001
# A-00003-0008 x
# A-00003-0010 x
# A-00003-0009 x
# A-00003-0011 x
# A-00003-0012 x
# A-00004-0003 x
# A-00004-0004 x


# A-00004-0012
# A-00004-0001 x
# A-00004-0008 x
# A-00004-0006 x
# A-00004-0009 x
# A-00004-0002 x
# A-00004-0005 x
# A-00004-0007 x
# A-00004-0010 x
# A-00004-0011 x
# A-00005-0002
# A-00005-0001
# A-00005-0003
# A-00005-0004
# A-00005-0005
# A-00005-0008
# A-00005-0012
# A-00005-0010
# A-00005-0009
# A-00005-0007
# A-00005-0011
# A-00005-0006
# A-00009-0004
# A-00009-0001
# A-00009-0005
# A-00009-0006 x
# A-00009-0007 x
