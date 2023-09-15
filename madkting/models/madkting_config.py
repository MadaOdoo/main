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
    _name = 'madkting.config'
    _description = 'Config'

    company_id = fields.Many2one('res.company', 'Company')
    stock_quant_available_quantity_enabled = fields.Boolean('Mostrar cantidad disponible', default=False)
    # stock_source = fields.Many2one('stock.location', string="Ubicacion de Stock", domain=[('usage', '=', 'internal')])
    stock_source_multi = fields.Char('Multi Stock Src')
    stock_source_channels = fields.Char('Channels Stock Src')
    webhook_stock_enabled = fields.Boolean('Stock webhooks enabled', default=False)
    simple_description_enabled = fields.Boolean('Simple Description product enabled', default=False)
    validate_barcode_exists = fields.Boolean('Validar si el codigo de barras existe', default=True)
    validate_sku_exists = fields.Boolean('Validar si el SKU existe', default=True)
    validate_id_exists = fields.Boolean('Validar si el Id Yuju existe', default=True)
    # update_partner_name = fields.Boolean("Update partner name with order ref")
    # update_partner_name_channel = fields.Char("Channels to update partner name with order ref")
    update_order_name = fields.Boolean("Update Order Name with Channel Ref")
    update_order_name_pack = fields.Boolean("Update Order Name with Pack")
    product_custom_fields = fields.Text("Product Custom fields")
    orders_unconfirmed = fields.Boolean('Ordenes sin confirmar', help='Deja las ordenes sin confirmar')
    orders_unconfirmed_by_stock = fields.Boolean('Validar stock para confirmar orden', help='Valida el stock de las ordenes antes de confirmar')
    orders_unconfirmed_by_ff_type = fields.Boolean('Validar fulfillment para confirmar orden', help='Valida el tipo de fulfillment ordenes antes de confirmar')
    orders_unconfirmed_stock_src = fields.Char(string="Ubicaciones para validar stock", help='Ubicaciones de stock para validar stock en ventas')
    orders_unconfirmed_ff_types = fields.Char(string="Tipos de Fulfillment para no confirmar ventas", help='Tipos de Fulfillment para validar ventas')
    # update_parent_list_price = fields.Boolean('Update Parent Price', help='Actualiza el precio del producto padre en caso de tener variantes')
    orders_force_cancel = fields.Boolean('Cancela ordenes con movimientos', help='Si esta habilitada las ordenes se cancelan incluso si tienen movimientos de almacen realizados.', default=True)
    orders_line_warehouse_enabled = fields.Boolean('Asigna almacen a las lineas de venta', help='Si esta habilitada se asigna el mismo almacen de la orden a las lineas de venta.', default=False)
    # order_disable_update_empty_fields = fields.Char('Campos que no se actualizan si estan vacios')
    order_remove_tax_default = fields.Boolean('Quitar impuestos default', help='Quita los impuestos default de las lineas de la venta')
    shipping_webhook_enabled = fields.Boolean(string="Enviar webhook de guia envio")
    validate_address_invoice = fields.Boolean(string="Validar direccion de envio para generar factura")
    required_invoice_address_fields = fields.Text('Campos requeridos factura')

    invoice_separator = fields.Char(string="Separador Serie y Folio", help='Indica el separador para acotar la serie y el folio de la factura')
    invoice_serie = fields.Char(string="Serie de la factura", help='Si esta definida, se utiliza como serie por default para la factura')
    invoice_partner_vat = fields.Char(string="RFC Cliente de las facturas", help='Si esta definido, se utiliza como VAT/RFC/TAXID por default para la factura')
    invoice_prefix_file = fields.Char(string="Prefijo del archivo", help='Se utiliza para identificar el archivo que va a procesarse por el modulo')
    invoice_prefix_pdf_file = fields.Char(string="Prefijo del archivo PDF", help='Se utiliza para identificar el archivo que va a procesarse por el modulo')
    # invoice_mimetype_file = fields.Char(string="Tipo de archivo", help='Se utiliza para identificar el Mimetype del archivo que va a procesarse por el modulo')
    invoice_add_pdf_file = fields.Boolean(string="Adjuntar archivo PDF", help='Se utiliza para adjuntar archivo PDF si existe.')
    invoice_save_pdf_attachment = fields.Boolean(string="Guardar Adjunto PDF", help='Se utiliza para guardar el archivo PDF Generado.')
    invoice_country = fields.Char(string="Codigo de Pais", help='Pais donde se esta emitiendo la factura (ISO 3166-1 alpha-3)')
    invoice_currency = fields.Char(string="Codigo de Moneda", help='Moneda utilizada para facturar (ISO 4227)')
    invoice_doc_type = fields.Selection([('ticket', "Nota/Boleta"), ("invoice", "Factura")], default="ticket", string="Tipo de documento facturacion")
    invoice_webhook_enabled = fields.Boolean(string="Enviar webhook de facturas")

    log_enabled = fields.Boolean('Habilitar log')

    dropship_enabled = fields.Boolean('Dropshiping Enabled')
    dropship_webhook_enabled = fields.Boolean('Dropshiping Webhook Enabled')
    dropship_stock_enabled = fields.Boolean('Stock Dropshiping Enabled')
    dropship_default_route_id = fields.Many2one('stock.route', string='Ruta Default para Dropshiping')
    dropship_route_id = fields.Many2one('stock.route', string='Ruta para Dropshiping')
    dropship_mto_route_id = fields.Many2one('stock.route', string='Ruta para MTO')
    dropship_picking_type = fields.Many2one('stock.picking.type', string='Dropship Picking Type')

    validate_partner_exists = fields.Boolean('Buscar Partner', help="Valida si existe el partner en odoo antes de crearlo")
    product_shared_catalog_enabled = fields.Boolean("Catalogo de productos compartido", default=False)
    service_url = fields.Char(string="Url servicio")
    
    @api.model
    def create_config(self, configs):
        """
        The config table is limited to only one record
        :param configs:
        :type configs: dict
        :return:
        """
        current_configs = self.get_config()

        if current_configs:
            return results.error_result('configurations_already_set')

        try:
            config = self.create(configs)
        except Exception as ex:
            logger.exception(ex)
            return results.error_result(ex)
        else:
            return results.success_result(config.copy_data()[0])

    @api.model
    def update_config(self, configs):
        """
        :param configs:
        :type configs: dict
        :return:
        """
        config = self.get_config()

        if not config:
            return results.error_result('configurations_not_set')
        try:
            config.write(configs)
        except Exception as ex:
            logger.exception(ex)
            return results.error_result(ex)
        else:
            return results.success_result(config.copy_data()[0])

    @api.model
    def get(self):
        """
        :return:
        :rtype: dict
        """
        config = self.get_config()

        if not config:
            return results.success_result()

        return results.success_result(config.copy_data()[0])

    def get_config(self):
        """
        Actualiza metodo para obtener configuracion de acuerdo al company del usuario
        :return:
        """
        # logger.debug("## GET CONFIG BY COMPANY ##")
        company_id = self.env.user.company_id.id
        # logger.debug(company_id)
        config_id = self.search([("company_id", "=", company_id)], limit=1)
        if not config_id:
            logger.debug("No se encontro config por company")
            config_id = self.search([], limit=1)
        # logger.debug(config_id)
        return config_id


class MadktingWebhook(models.Model):
    _name = 'madkting.webhook'
    _description = 'Web hooks'

    __allowed_hook_types = ['stock']

    hook_type = fields.Char('Webhook type', size=20, required=True)
    url = fields.Char('Web hooks url', size=400, required=True)
    active = fields.Boolean('Active', default=True, required=True)
    company_id = fields.Many2one('res.company', 'Company')

    # _sql_constraints = [
    #     ('unique_webhook_company', 'unique(hook_type,company_id)', 'The webhook should be unique per company')
    # ]

    @api.model
    def get(self, hook_id=None, hook_type=None):
        """
        :param hook_id:
        :type hook_id: int
        :param hook_type:
        :type hook_type: str
        :return:
        :rtype: dict
        """
        if hook_id:
            webhook = self.search([('id', '=', hook_id)], limit=1)

            if not webhook:
                return results.error_result(
                    'not_exists',
                    'The resource that you are looking for doesn\'t exists or has been deleted'
                )
            return results.success_result(webhook.__get_data())

        if hook_type:
            if hook_type not in self.__allowed_hook_types:
                return results.error_result('invalid_hook_type')

            webhooks = self.search([('hook_type', '=', hook_type)])
        else:
            webhooks = self.search([])

        if not webhooks:
            return results.success_result([])

        data = list()

        for hook in webhooks:
            data.append(hook.__get_data())

        return results.success_result(data)

    @api.model
    def create_webhook(self, hook_type, url, company_id):
        """
        :param hook_type:
        :type hook_type: str
        :param url:
        :type url: str
        :return:
        :rtype: dict
        """
        if hook_type not in self.__allowed_hook_types:
            return results.error_result('invalid_hook_type')

        parse_result = parse.urlparse(url)

        if not parse_result.scheme or not parse_result.netloc:
            return results.error_result('invalid_hook_url')

        try:
            webhook = self.create({
                'hook_type': hook_type,
                'url': url,
                'active': True,
                'company_id' : company_id
            })
        except Exception as ex:
            logger.exception(ex)
            return results.error_result('create_webhook_error', str(ex))
        else:
            return results.success_result(webhook.__get_data())

    @api.model
    def update_webhook(self, hook_id, **kwargs):
        """
        :param hook_id:
        :type hook_id:  int
        :param kwargs:
        :return:
        :rtype: dict
        """
        webhook = self.search([('id', '=', hook_id)], limit=1)

        if not webhook:
            return results.error_result(
                    'not_exists',
                    'The resource that you are looking for doesn\'t exists or has been deleted'
                )
        try:
            webhook.write(kwargs)
        except Exception as ex:
            logger.exception(ex)
            return results.error_result('write_exception', str(ex))
        else:
            return results.success_result(webhook.__get_data())

    @api.model
    def activate(self, hook_id):
        """
        :param hook_id:
        :return:
        """
        webhook = self.search([('id', '=', hook_id)], limit=1)

        if not webhook:
            return results.error_result(
                    'not_exists',
                    'The resource that you are looking for doesn\'t exists or has been deleted'
                )

        return webhook.change_status(active=True)

    @api.model
    def deactivate(self, hook_id):
        """
        :param hook_id:
        :return:
        """
        webhook = self.search([('id', '=', hook_id)], limit=1)

        if not webhook:
            return results.error_result(
                    'not_exists',
                    'The resource that you are looking for doesn\'t exists or has been deleted'
                )

        return webhook.change_status(active=False)

    def change_status(self, active):
        """
        :param active:
        :type active: bool
        :return:
        :rtype: dict
        """
        self.ensure_one()
        try:
            self.active = active
        except Exception as ex:
            logger.exception(ex)
            return results.error_result('activate_webhook_exception')
        else:
            return results.success_result()

    def __get_data(self):
        """
        :return:
        :rtype: dict
        """
        self.ensure_one()
        data = self.copy_data()[0]
        data['id'] = self.id
        return data
