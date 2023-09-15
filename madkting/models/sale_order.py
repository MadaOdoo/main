# -*- coding: utf-8 -*-
# File:           sale_order.py
# Author:         Israel Calderón
# Copyright:      (C) 2019 All rights reserved by Madkting
# Created:        2019-03-20
import requests
import base64

from odoo import models, fields, api
from odoo import exceptions
from datetime import datetime
from ..log.logger import logger
from ..responses import results


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    channel = fields.Char('Marketplace')
    channel_id = fields.Integer('Channel Id')
    yuju_shop_id = fields.Integer('Yuju Shop Id')
    
    yuju_pack_id = fields.Char('Yuju Pack Id')
    yuju_shipping_id = fields.Char('Yuju Item Shipping')
    yuju_seller_id = fields.Char('Yuju Seller Id')
    yuju_marketplace_fee = fields.Float("Marketplace Fee")
    yuju_seller_shipping_cost = fields.Float("Seller Shipping Cost")
    yuju_carrier_tracking_ref = fields.Char("Numero de Guia")
    yuju_update_date_order = fields.Char("Fecha Actualizacion Yuju")
    yuju_payment_date_order = fields.Char("Fecha Acreditacion Pago")

    fulfillment = fields.Selection([
        ('mix', 'Mix'),
        ('fbf', 'Flex'),
        ('fbm', 'Seller'),
        ('fbc', 'Full'),
        ], string="Fulfillment")
    channel_order_reference = fields.Char('Marketplace Reference')
    channel_order_id = fields.Char('Marketplace Id')
    channel_order_market_fee = fields.Float('Channel Marketplace Fee')
    channel_order_shipping_cost = fields.Float('Shipping Cost')
    yuju_url_label = fields.Text('Label URL')


    order_progress = fields.Char('Order Progress')
    payment_status = fields.Char('Payment Status')
    payment_id = fields.Integer('Pago Id')

    def _update_mapping_fields(self, order_data):
        order_data = self.env['yuju.mapping.field'].update_mapping_fields(order_data, 'sale.order')
        return order_data

    def _update_custom_values(self, fulfillment, channel_id):
        logger.debug("## CUSTOM VALUES FOR ORDERS ##")
        customs = self.env['yuju.mapping.custom'].update_custom_values(fulfillment, channel_id, modelo='sales')
        logger.debug(customs)
        return customs

    def _get_defect_values(self, modelo='sales'):
        logger.debug("## DEFAULT VALUES FOR ORDERS ##")
        defaults = self.env['yuju.mapping.custom'].get_defect_values(modelo)
        logger.debug(defaults)
        return defaults

    @api.model
    def mdk_create(self, order_data, **kwargs):
        """
        :param order_data:
        {
            'company_id': int,
            'date_order': str,
            'validity_date': str, # YYYY-mm-dd
            'confirmation_date': str, # deprecated
            'note': str,
            'partner_id': int,
            'invoice_status': str,
            'warehouse_id': int,
            'channel': str, # madkting
            'channel_id': int, # madkting
            'channel_order_reference': str, # madkting
            'channel_order_id': str, # madkting
            'order_progress': str, # madkting
            'payment_status': str, # madkting
            'lines': [
                {
                    # 'order_id': int,
                    'name': str,
                    'sequence': int, # 10
                    'invoice_status': str, # 'to invoice'
                    'price_unit': float,
                    'price_subtotal': float,
                    'price_tax': float,
                    'price_total': float,
                    'price_reduce': float,
                    'price_reduce_taxinc': float,
                    'price_reduce_taxexcl': float,
                    'discount': float,
                    'product_id': int,
                    'product_uom_qty': float,
                    'product_uom': int,
                    'qty_delivered_method': str, #'stock_move'
                    'qty_delivered': float,
                    # 'qty_delivered_manual': float,
                    'qty_to_invoice': float,
                    'qty_invoiced': float,
                    'untaxed_amount_invoiced': float,
                    'untaxed_amount_to_invoice': float,
                    'salesman_id': int,
                    'currency_id': int, # search for id  based on currency key "MXN"
                    'company_id': int, # mapped by user
                    'order_pmdk_crtr, # 'sale'
                    'customer_lead': int, # 0
                    'tax_rate': bool,
                }
            ]
        }
        :type order_data: dict
        :param kwargs:
            :tax_rate: int
            :set_tax_rate_by_product: bool
            :force_creation: bool
        :return: new sale.order
        :rtype: sale.order
        """
        logger.debug("### MDK CREATE ###")
        logger.debug(order_data)
        config = self.env['madkting.config'].get_config()
        order_data.pop('confirmation_date', None)
        config_settings = self.env['res.config.settings']
        picking_policy = config_settings.default_picking_policy
        tax_rate = kwargs.get('tax_rate')
        set_tax_rate_by_product = kwargs.get('set_tax_rate_by_product')
        force_creation = kwargs.get('force_creation')
        company_id = order_data.get('company_id')

        if not picking_policy:
            picking_policy = 'direct'

        order_data['require_signature'] = False
        order_data['require_payment'] = True
        """
        # TODO: if a client has prices list enabled may cause conflicts since
        # the orders from marketplaces may not match client prices list data
        """
        """
        # Verifica si se envia lista de precios personalizada, y si esta existe en el sistema
        # en caso de que no exista o no se envie, se define la lista de precios default.
        """
        if "pricelist_id" in order_data:
            pricelist_id = order_data["pricelist_id"]
            pricelist_ids = self.env["product.pricelist"].search([('id', '=', pricelist_id)], limit=1)
            if not pricelist_ids:
                order_data['pricelist_id'] = 1
        else:
            order_data['pricelist_id'] = 1

        order_data['state'] = 'draft'
        order_data['picking_policy'] = picking_policy

        if not order_data.get('date_order'):
            order_data['date_order'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        if not order_data.get('invoice_status'):
            order_data['invoice_status'] = 'to invoice'

        if not config:
            return results.error_result(code='sale_config_error',
                                        description='No config found for this company')

        if config and config.dropship_enabled:
            route_ids = []
            if config.dropship_default_route_id:
                route_ids.append(config.dropship_default_route_id.id)
            if config.dropship_route_id:
                route_ids.append(config.dropship_route_id.id)
            if config.dropship_mto_route_id:
                route_ids.append(config.dropship_mto_route_id.id)
            
            if not route_ids:
                return results.error_result(code='sale_config_dropship_error',
                                            description='No config routes found for dropship')   

        order_data = self._update_mapping_fields(order_data)

        logger.debug("## FIELD ERRORS ##")
        field_errors = self._validate_order_fields(order_data=order_data)
        logger.debug(field_errors)
        if field_errors:
            return results.error_result(code='required_fields_validation',
                                        description=', '.join(field_errors))
        tax_cache = dict()
        if tax_rate:
            tax_cache[tax_rate] = self.env['account.tax'] \
                                      .search([('type_tax_use', '=', 'sale'),
                                               ('amount', '=', tax_rate),
                                               ('active', '=', True),
                                               ('company_id', '=', company_id)],
                                              limit=1)
        lines = order_data.pop('lines')
        logger.debug("### ORDER DATA ###")
        logger.debug(order_data)

        if order_data.get('channel_order_id') and order_data.get('channel_id'):
            _channel_id = order_data.get('channel_id')
            _channel_order_id = order_data.get('channel_order_id')
            _ff_type = order_data.get('fulfillment')
            domain = [('channel_order_id', '=', _channel_order_id), ('channel_id', '=', _channel_id), ("fulfillment", "=", _ff_type)]
            order_exists = self.search(domain, limit=1)
            if not force_creation and order_exists:
                logger.debug("### ORDER EXISTS {} ###".format(order_data.get("channel_order_reference")))
                
                if order_exists.state in ['draft', 'sent']:
                    try:
                        self._confirma_orden(order_exists)
                    except Exception as ex:
                        post_message = 'The sale order counldn\'t be confirmed because of the following exception: {}'.format(ex)
                        logger.debug(post_message)
                        order_exists.message_post(body=post_message)

                data=order_exists.yuju_get_data()
                logger.debug("### RESPONSE MDK CREATE EXISTS ####")
                logger.debug(data)
                return results.success_result(data)

        if order_data.get('yuju_pack_id'):
            order_exists = self.search([('yuju_pack_id', '=', order_data.get("yuju_pack_id"))], limit=1)
            if not force_creation and order_exists:
                logger.debug("### ORDER EXISTS {} ###".format(order_data.get("yuju_pack_id")))
                
                if order_exists.state in ['draft', 'sent']:
                    try:
                        self._confirma_orden(order_exists)
                    except Exception as ex:
                        post_message = 'The sale order counldn\'t be confirmed because of the following exception: {}'.format(ex)
                        logger.debug(post_message)
                        order_exists.message_post(body=post_message)

                data=order_exists.yuju_get_data()
                logger.debug("### RESPONSE MDK CREATE EXISTS PACK ####")
                logger.debug(data)
                return results.success_result(data)

        # if config.orders_unconfirmed:
        #     order_data.update({'state' : 'draft'})

        warehouse_id = order_data.get('warehouse_id')

        if order_data.get('fulfillment') and order_data.get('channel_id'):
            fulfillment = order_data.get('fulfillment')
            channel_id = order_data.get('channel_id')
            custom_data = self._update_custom_values(fulfillment, channel_id)
            if custom_data:
                logger.debug("## ORDER DATA CUSTOM ###")
                order_data.update(custom_data)
                logger.debug(order_data)
        try:
            new_sale = self.create(order_data)

            if new_sale:
                if config.update_order_name:
                    new_sale.write({"name" : order_data.get("channel_order_reference")})

                if config.update_order_name_pack and new_sale.yuju_pack_id:
                    new_sale.write({"name" : order_data.get("yuju_pack_id")})

                # if config.update_partner_name and config.update_partner_name_channel:
                #     channel_ids = config.update_partner_name_channel.split(",")
                #     channel_ids = [int(i) for i in channel_ids]

                #     if new_sale.channel_id in channel_ids:
                #         partner = new_sale.partner_id
                #         if partner.name.find(new_sale.name) < 0:
                #             partner.write({"name" : "{}, {}".format(partner.name, new_sale.name)})

        except exceptions.AccessError as err:
            logger.exception(err)
            return results.error_result(
                code='access_error',
                description=str(err)
            )
        except Exception as ex:
            logger.exception(ex)
            return results.error_result(
                code='sale_create_error',
                description='The sale order counldn\'t be created because of the following exception: {}'
                .format(ex)
            )
        else:
            order_line_model = self.env['sale.order.line']
            for line in lines:
                
                # Clear fields odoo V16
                logger.info("## Clear fields Odoo 16 ##")
                logger.info(order_data)
                remove_line_fields = ['qty_delivered_manual']
                for field in remove_line_fields:
                    if field in line:
                        logger.info(f"## Remove field ## {field}")
                        line.pop(field)

                product_tax_rate = line.pop('tax_rate', False)
                line['order_id'] = new_sale.id
                line['state'] = 'draft'

                product = self.env['product.product'].search([('id', '=', int(line.get('product_id')))], limit=1)

                if config.orders_line_warehouse_enabled and warehouse_id:
                    line.update({'warehouse_id' : warehouse_id})

                if config.dropship_enabled and new_sale.warehouse_id.dropship_enabled:
                    route = config.dropship_default_route_id
                    logger.debug("## AGREGAR RUTA DROPSHIP ###")
                    logger.debug("## RUTA: {} ###".format(route.name))
                    if product.id and product.type == 'product':
                        logger.debug("## ID RUTA: {}".format(route.id))
                        location_stock = new_sale.warehouse_id.lot_stock_id
                        logger.debug("## LOCATION STOCK: {}".format(location_stock.id))
                        qty_in_branch = product.with_context({'location' : location_stock.id}).qty_available
                        # qty_in_branch = self.env['stock.quant']._get_available_quantity(product, location_stock)
                        logger.debug("## QTY IN BRANCH: {}".format(qty_in_branch))
                        if qty_in_branch < line.get('product_uom_qty', 0):
                            if product.tipo_producto_yuju and product.tipo_producto_yuju == "dropship":
                                route = config.dropship_route_id
                            elif product.tipo_producto_yuju and product.tipo_producto_yuju == "mto":
                                route = config.dropship_mto_route_id
                            line.update({"route_id" : route.id})

                # if config.orders_unconfirmed:
                #     line.update({'state' : 'draft'})
                
                # YUJU envia la UDM Pieza(s) Id:1, lo cual genera un problema con 
                # productos que manejan otras unidades de medida.
                line_product_uom_id = int(line.get('product_uom'))
                if product.uom_id.id != line_product_uom_id:
                    line['product_uom'] = product.uom_id.id

                try:
                    logger.debug(line)
                    new_line = order_line_model.sudo().create(line)
                except exceptions.AccessError as err:
                    logger.exception(err)
                    # TODO: cancel sale before delete
                    cancel_sale = new_sale.action_cancel()
                    if cancel_sale:
                        new_sale.sudo().unlink()
                    return results.error_result(
                        code='sale_line_access_error',
                        description='An exception has occurred trying to '
                                    'create a sale line for product {}. '
                                    'The transaction has been rolledback. '
                                    'Exception: {}'.format(line.get('product_id'), err)
                    )
                except Exception as lex:
                    logger.exception(lex)
                    # TODO: cancel sale before delete
                    cancel_sale = new_sale.action_cancel()
                    if cancel_sale:
                        new_sale.sudo().unlink()
                    return results.error_result(
                        code='sale_create_line_error',
                        description='An exception has occurred trying to '
                                    'create a sale line for product {}. '
                                    'The transaction has been rolledback. '
                                    'Exception: {}'.format(line.get('product_id'), lex)
                    )
                else:                    
                    if not set_tax_rate_by_product and tax_cache.get(tax_rate):
                        new_line.tax_id = tax_cache[tax_rate]
                        continue
                    if set_tax_rate_by_product and product_tax_rate:
                        if not tax_cache.get(product_tax_rate):
                            tax_cache[product_tax_rate] = self.env['account.tax'] \
                                                              .search([('type_tax_use', '=', 'sale'),
                                                                       ('amount', '=', product_tax_rate),
                                                                       ('active', '=', True),
                                                                       ('company_id', '=', company_id)],
                                                                      limit=1)
                        new_line.tax_id = tax_cache.get(product_tax_rate)

                    if new_line.tax_id and config.order_remove_tax_default and not tax_rate and not set_tax_rate_by_product:
                        logger.info(
                            "Se quitan impuestos por default si no se recibe impuesto desde Yuju")
                        new_line.tax_id = [(6, 0, [])]
                        continue

            try:
                # raise ValueError('Error on process..')
                if not config.orders_unconfirmed:
                    self._confirma_orden(new_sale)
                else:
                    logger.debug('orders_unconfirmed, the order should be confirmed manually')
            except Exception as ex:
                # new_sale.unlink()
                post_message = 'The sale order counldn\'t be confirmed because of the following exception: {}'.format(ex)
                logger.debug(post_message)
                new_sale.message_post(body=post_message)
                # return results.error_result(
                #     code='sale_confirm_error',
                #     description='The sale order counldn\'t be confirmed because of the following exception: {}'.format(ex))
            else:
                new_sale.add_order_message("shipping")

            data=new_sale.yuju_get_data()
        # logger.debug("### RESPONSE MDK CREATE ####")
        # logger.debug(data)
        return results.success_result(data)

    def yuju_get_data(self):
        """
        :return: dictionary with sale order data
        :rtype: dict
        """
        self.ensure_one()
        data = self.copy_data()[0]
        data['lines'] = list()
        extra_fields = ['id', 'name', 'state', 'amount_total', 'amount_tax',
                        'amount_undiscounted', 'amount_untaxed',
                        'invoice_ids', 'picking_ids']

        line_extra_fields = ['id', 'order_id', 'invoice_status', 'price_subtotal',
                             'price_tax', 'price_total', 'price_reduce',
                             'price_reduce_taxinc', 'price_reduce_taxexcl',
                             'qty_delivered_method', 'qty_delivered',
                             'qty_to_invoice',
                             'qty_invoiced', 'untaxed_amount_invoiced',
                             'untaxed_amount_to_invoice', 'salesman_id',
                             'currency_id', 'company_id', 'order_partner_id']

        one_to_many_ids = ['invoice_ids', 'picking_ids']
        many_to_one_ids = ['order_id', 'salesman_id', 'currency_id',
                           'company_id', 'order_partner_id']

        for field in extra_fields:
            data[field] = getattr(self, field, False)
            if field in one_to_many_ids:
                data[field] = [int(id_) if id_ else bool(id_) for id_ in data[field]]

        for line in self.order_line:
            line_data = line.copy_data()[0]
            for line_field in line_extra_fields:
                line_data[line_field] = getattr(line, line_field, False)
                if line_field in many_to_one_ids:
                    line_data[line_field] = int(line_data[line_field]) if line_data[line_field] \
                                            else bool(line_data[line_field])
            data['lines'].append(line_data)

        data['create_date'] = self.create_date.isoformat(' ')
        data.pop('order_line')
        return data

    def tiene_stock(self):
        config = self.env['madkting.config'].get_config()
        orders_unconfirmed_stock_src = config.orders_unconfirmed_stock_src
        logger.info(f"Locations to validate stock: {orders_unconfirmed_stock_src}")
        for line in self.order_line:
            product = line.product_id
            logger.info(f"Producto: {product.id} - {product.default_code}")
            total = 0
            location_stock = ''
            for location_id in orders_unconfirmed_stock_src.split(','):
                location = self.env['stock.location'].search([('id', '=', int(location_id))], limit=1)
                logger.info(f"Location: {location.id} - {location.name}")
                qty_in_branch = product.with_context({'location' : location.id}).free_qty
                # qty_in_branch = self.env['stock.quant']._get_available_quantity(product, location)
                logger.info(f"Quantity for: {qty_in_branch}")
                location_stock = f'{location_stock} Location: {location.name}, Stock: {qty_in_branch}, '
                if qty_in_branch:
                    total += int(qty_in_branch)            
            logger.info(f"Total: {total}")
            post_message = f"Product {product.default_code}, {location_stock}."
            self.message_post(body=post_message)
        

    def _has_stock(self, product, location):
        logger.info(f"Valida Stock Location: {location.id}")
        total = 0
        # qty_in_branch = self.env['stock.quant']._get_available_quantity(product, location)
        qty_in_branch = product.with_context({'location' : location.id}).free_qty
        logger.info(f"QTY IN BRANCH: {qty_in_branch}")

        if qty_in_branch:
            total += int(qty_in_branch)

        if total > 0:
            return total

        return False

    def _valida_stock_productos(self, order):
        location = order.warehouse_id.lot_stock_id
        for line in order.order_line:
            product = line.product_id
            if product.detailed_type != 'product':
                continue
            stock_product = self._has_stock(product, location)
            if not stock_product:
                post_message = f"Error trying to confirm order, product {product.default_code} insufficient stock 0, Location: {location.name}."
                order.message_post(body=post_message)
                return False
            else:
                if line.product_uom_qty > stock_product:                   
                    post_message = f"Error trying to confirm order, product {product.default_code} insufficient stock {stock_product}, Location: {location.name}."
                    order.message_post(body=post_message)
                    return False
        return True

    def _confirma_orden(self, order):
        config = self.env['madkting.config'].get_config()
        to_confirm = True
        if config.orders_unconfirmed_by_stock:
            to_confirm = self._valida_stock_productos(order)  

        if to_confirm and config.orders_unconfirmed_by_ff_type:
            logger.debug("Valida tipo de Fulfillment para confirmar la orden")
            fulfillments = config.orders_unconfirmed_ff_types.split(',')
            logger.debug(f"Fulfillments para validar {fulfillments}")
            logger.debug(f"Order Fulfillment {order.fulfillment}")
            if fulfillments:
                if order.fulfillment in fulfillments:
                    logger.debug("No se confirma..")
                    to_confirm = False
                    post_message = f"El tipo de fulfillment es [{order.fulfillment}], no se confirma la orden"
                    order.message_post(body=post_message)
                              
        if to_confirm:
            order.action_confirm()

    @api.model
    def update_order(self, order_id, order_data):
        """
        Update order attributes (order lines not supported yet)
        :param order_id: order to update
        :type order_id: int
        :param order_data: attributes to update in sale order
        :type order_data: dict
        :return:
        :rtype: dict
        """
        order = self.search([('id', '=', order_id)])
        config = self.env['madkting.config'].get_config()

        logger.debug("## UPDATE ORDER ##")
        logger.debug(order_data)

        if not order:
            return results.error_result(code='sale_not_exists',
                                        description='order {} doesn\'t exists'.format(order_id))
        order.ensure_one()
        updatable_attributes = ['note', 'partner_shipping_id', 'partner_invoice_id',
                                'validity_date', 'order_progress', 'yuju_update_date_order',
                                'yuju_payment_date_order', 'yuju_carrier_tracking_ref',
                                'yuju_url_label'
                                ]

        updates = {attribute: value for attribute, value in order_data.items() if attribute in updatable_attributes}

        if not updates:
            return results.error_result(code='not_valid_data',
                                        description='The attributes you\'re trying to update are invalid')

        if order.state in ['draft', 'sent'] and config and not config.orders_unconfirmed:
            try:       
                self._confirma_orden(order)
            except Exception as ex:
                return results.error_result(
                    code='sale_confirm_error',
                    description='The sale order counldn\'t be confirmed because of the following exception: {}'.format(ex))

        logger.debug("#### UPDATE ORDER ####")
        logger.debug(updates)

        try:
            order.write(updates)
        except Exception as ex:
            return results.error_result(code='sale_update_error',
                                        description=str(ex))
        else:
            return results.success_result()


    @api.model
    def deliver_order(self, order_id=None, order=None, **kwargs):
        """
        :param order_id: sale order id
        :type order_id: int
        :param order: sale.order record
        :type order: odoo.api.sale.order
        :keyword kwargs:
            default_sale_products_origin int
            default_sale_products_destiny int
            picking_type_id int
            state str # 'done', 'draft', 'cancel', 'ready'
        :return:
        """
        logger.debug("### DELIVER ORDER ###")
        logger.debug(order_id)
        logger.debug(order)
        logger.debug(kwargs)
        config = self.env['madkting.config'].get_config()

        if not order and not order_id:
            return results.error_result(code='missing_order_id',
                                        description='You must provide at least order_id')

        elif not order and order_id:
            order = self.search([('id', '=', order_id)])

        if not order or not order.id:
            return results.error_result(code='sale_not_exists',
                                        description='order {} doesn\'t exists'.format(order_id))

        if order.state not in ['sale', 'done']:
            return results.error_result(code='order_unconfirmed',
                                        description='You must confirm the order_id to deliver')

        if not order.picking_ids:
            return results.error_result(code='no_picking_found',
                                        description='picking doesn\'t exists')

        if not kwargs.get('state'):
            return results.error_result(code='missing_state_argument',
                                        description='delivery state is mandatory')

        order.ensure_one()
        current_delivery = False
        outgoing_picking = False

        if config.dropship_enabled and config.dropship_picking_type:

            for picking in order.picking_ids:
                picking_type = picking.picking_type_id
                if picking_type.id == config.dropship_picking_type.id:
                    logger.debug("## DROPSHIP OPERATION ##")
                    current_delivery = picking
                    current_id = current_delivery.id
                    current_name = current_delivery.name
                    current_data = current_delivery.copy_data()[0]

                    current_data['id'] = current_id
                    current_data['name'] = current_name
                    current_data['state'] = current_delivery.state
                    return results.success_result(data=current_data)

        for picking in order.picking_ids:
            picking_type = picking.picking_type_id
            logger.debug("## PICKING TYPE ##")
            logger.debug(picking_type.code)

            if picking_type.code != 'outgoing':
                logger.debug("## Next picking ##")
                continue            

            outgoing_picking = True
            current_delivery = picking

            if current_delivery.state == "waiting":
                 logger.debug("Algunos picking estan esperando otra operacion, no se pueden confirmar.")
                 return results.error_result(code='picking_pending_state',
                                         description='Some pickings are on pending state can\'t confirm')

            if current_delivery.state == 'confirmed':
                logger.debug('confirmed')
                try:
                    current_delivery.action_assign()
                except Exception as e:
                    post_message = "Error trying to assign delivery {}.".format(e)
                    logger.debug(post_message)
                    current_delivery.message_post(body=post_message)
                    return results.error_result(code='no_picking_assigned',
                                        description='cannot assign order picking')
                else:
                    if current_delivery.state == "assigned":
                        post_message = 'Delivery Assigned.'
                    else:
                        post_message = 'Cannot assign reserved quantity, please verify stock.'
                    current_delivery.message_post(body=post_message)

            if current_delivery.state == 'assigned':
                logger.debug('assigned')
                try:
                    for line in current_delivery.move_line_ids.sudo():
                        line.sudo().write({
                            'qty_done': line.reserved_uom_qty
                        })
                    current_delivery.button_validate()
                except Exception as e:
                    post_message = "Error trying to complete delivery {}.".format(e)
                    logger.debug(post_message)
                    current_delivery.message_post(body=post_message)
                    return results.error_result(code='no_picking_done',
                                        description='cannot complete order picking')
                else:
                    if current_delivery.state == "done":
                        post_message = 'Delivery Done.'
                    else:
                        post_message = 'Cannot complete delivery, please retry.'
                    current_delivery.message_post(body=post_message)

            if current_delivery.state == "done":
                logger.debug("## PICKING DONE ##")
                break
            
        if not outgoing_picking:
            logger.debug("No se encontro ningun picking de tipo salida de almacen")
            return results.error_result(code='no_picking_found',
                                        description='picking doesn\'t exists')

        if current_delivery.state != 'done':
            logger.debug("No se pudo finalizar la entrega, es necesario reintentar")
            return results.error_result(code='picking_needs_retry',
                                        description='picking needs retry to complete')

        current_id = current_delivery.id
        current_name = current_delivery.name
        current_data = current_delivery.copy_data()[0]

        current_data['id'] = current_id
        current_data['name'] = current_name
        current_data['state'] = current_delivery.state

        return results.success_result(data=current_data)

    @api.model
    def supplier_invoice_order(self, order_id, partner_id, shipping_id, fee_id):
        """
        :param order_id:
        :type order_id: int
        :return:
        """

        logger.debug("SUPPLIER INVOICES")

        if not order_id:
            return results.error_result(code='order_id_required',
                                        description='order_id is required')
        order = self.search([('id', '=', order_id)])

        if not order:
            return results.error_result(code='sale_not_exists',
                                        description='order {} doesn\'t exists'.format(order_id))
        order.ensure_one()

        if not order.invoice_ids:
            return results.error_result(code='sale_not_exists',
                                        description='order {} doesn\'t exists'.format(order_id))

        if order.invoice_ids:
            invoice = order.invoice_ids
            invoice.ensure_one()
            # if invoice is cancelled skip this and try to create it
            if invoice.state == 'posted': 
                create = False
                if order.channel_order_shipping_cost > 0 or order.channel_order_market_fee > 0:
                    data = {
                        'partner_id': partner_id,
                        'date' : datetime.now().strftime('%Y-%m-%d'),
                        'type' : 'in_invoice',
                        # 'state': 'draft',
                        'invoice_origin' : order.name,
                        'ref' : order.name,
                        'invoice_line_ids' : []
                    }
                    if order.channel_order_shipping_cost and shipping_id:
                        product_ids = self.env['product.product'].search([('id', '=', shipping_id)])
                        if product_ids:
                            data['invoice_line_ids'].append((0, 0, {
                                    'product_id' : shipping_id,
                                    'quantity' : 1,
                                    'price_unit' : order.channel_order_shipping_cost,
                                    }))
                            create = True

                    if order.channel_order_market_fee and fee_id:
                        product_ids = self.env['product.product'].search([('id', '=', fee_id)])
                        if product_ids:
                            data['invoice_line_ids'].append((0, 0, {
                                    'product_id' : fee_id,
                                    'quantity' : 1,
                                    'price_unit' : order.channel_order_market_fee,
                                    }))
                            create = True

                    if partner_id:
                        partner_ids = self.env['res.partner'].search([('id', '=', partner_id)])
                        if not partner_ids:
                            create = False
                            return results.error_result(code='sale_not_exists',
                                        description='The sale order cannot be supplier invoiced because the supplier {} does not exists'.format(partner_id))
                    else:
                        create = False
                        return results.error_result(code='sale_not_exists',
                                        description='The sale order cannot be supplier invoiced because the supplier {} does not exists'.format(partner_id))
                    logger.debug(data)
                    facturas = self.env['account.move']
                    invoice_exists = facturas.search([('ref', '=', order.name), ('type', '=', 'in_invoice')])
                    if not invoice_exists:
                        if create:
                            try:
                                supplier_invoice = facturas.create(data)
                            except Exception as ex:
                                logger.exception(ex)
                                return results.error_result(code='invoice_create_error',
                                                            description='The sale order cannot be supplier invoiced because of '
                                                                        'the following exception: {}'.format(ex))
                            else:
                                invoice_data = supplier_invoice.copy_data()[0]
                                invoice_data['id'] = supplier_invoice.id
                                invoice_data['name'] = supplier_invoice.name
                                return results.success_result(data=invoice_data)
                    else:
                        logger.debug('Invoice exists')
                        logger.debug(invoice_exists)
                        invoice_data = invoice_exists.copy_data()[0]
                        return results.success_result(data=invoice_data)

        return results.error_result(code='invoice_create_error',
                                        description='The sale order cannot be supplier invoiced')

    def _is_invoice_address_complete(self, invoice_address):
        logger.info("## Validar direccion de factura ##")
        config = self.env['madkting.config'].get_config()
        if config.required_invoice_address_fields:
            required_fields = config.required_invoice_address_fields.split(',')
            logger.info(f"Campos requeridos {required_fields}")
            partner_data = None
            partner_ids = self.env["res.partner"].search([("id", "=", invoice_address.id)], limit=1)
            
            not_found = []
            if partner_ids:
                
                partner_data = partner_ids.read([])
                # logger.info(f"Address data {partner_data}")

                is_complete = True
            
                for field in required_fields:
                    if not partner_data[0].get(field):
                        is_complete = False
                        not_found.append(field)
                
                if is_complete:
                    return True, []

        return False, not_found
            
    @api.model
    def invoice_order(self, order_id):
        """
        :param order_id:
        :type order_id: int
        :return:
        """
        if not order_id:
            return results.error_result(code='order_id_required',
                                        description='order_id is required')
        order = self.search([('id', '=', order_id)])

        if not order:
            return results.error_result(code='sale_not_exists',
                                        description='order {} doesn\'t exists'.format(order_id))

        if order.state not in ['sale', 'done']:
            return results.error_result(code='sale_not_confirmed',
                                        description='order {} is not confirmed'.format(order_id))

        config = self.env['madkting.config'].get_config()
        
        order.ensure_one()

        if order.invoice_ids:
            for invoice in order.invoice_ids:
            # invoice = order.invoice_ids
            # invoice.ensure_one()
            # if invoice is cancelled skip this and try to create it
                if invoice.state != 'cancel':
                    if invoice.state not in ['posted', 'paid', 'ready']:                    
                        invoice.action_post()
                    invoice_data = invoice.copy_data()[0]
                    invoice_data['id'] = invoice.id
                    invoice_data['name'] = invoice.name
                    invoice_data['state'] = invoice.state
                    return results.success_result(data=invoice_data)

        if config.validate_address_invoice:
            invoice_complete, not_found_fields = self._is_invoice_address_complete(order.partner_invoice_id)
            logger.info(invoice_complete)
            logger.info(not_found_fields)

            if not invoice_complete:
                return results.error_result(code='invoice_confirm_error',
                                    description='The invoice cannot be confirmed because of '
                                                f'invoice address is not complete {not_found_fields}') 

        try:
            invoice = order.sudo()._create_invoices(grouped=True)
        except exceptions.AccessError as err:
            return results.error_result(
                code='access_error',
                description=str(err)
            )
        except Exception as ex:
            logger.exception(ex)
            return results.error_result(code='invoice_create_error',
                                        description='The sale order cannot be invoiced because of '
                                                    'the following exception: {}'.format(ex))
        else:            
            invoice.ensure_one()
            defaults = self._get_defect_values('invoices')        
            if defaults:
                try:
                    logger.debug("## DEFAULT INVOICES ###")
                    logger.debug(defaults)
                    invoice.update(defaults)
                except Exception as e:
                    logger.exception(f'Error al actualizar los datos de la factura: {e}')
                    return results.error_result(code='invoice_create_error',
                                        description='The sale order cannot be invoiced because of '
                                                    'the following exception: {}'.format(e))
            try:
                invoice.action_post()
            except Exception as e:
                logger.exception(f'Error al actualizar los datos de la factura: {e}')
                return results.error_result(code='invoice_confirm_error',
                                    description='The sale order invoice cannot be confirmed because of '
                                                'the following exception: {}'.format(e))

            invoice_data = invoice.copy_data()[0]
            invoice_data['id'] = invoice.id
            invoice_data['name'] = invoice.name
            invoice_data['state'] = invoice.state

            order.add_order_message("invoice")

            return results.success_result(data=invoice_data)

    def test_send_invoice_xml(self):
        logger.info("TESTING SEND XML")
        for rec in self:
            res = rec.add_order_message("invoice")
            logger.info(res)

    def test_send_shipping(self):
        logger.info("TESTING SEND SHIPPING")
        for rec in self:
            res = rec.add_order_message("shipping")
            logger.info("## RESPONSE ##")
            logger.info(res)

    def test_print_invoice(self):
        logger.info("TESTING PRINT INVOICE")
        for rec in self:
            self.print_invoice(rec.id)

    def validate_action_message(self, action):
        
        config = self.env['madkting.config'].get_config()
        
        if action == 'shipping' and not config.shipping_webhook_enabled:
            return False

        elif action == 'invoice' and not config.invoice_webhook_enabled:
            return False

        return True

    def add_order_message(self, action="shipping"):

        logger.info(f"PREPARING MESSAGE {action}")

        config = self.env['madkting.config'].get_config()

        if not self.validate_action_message(action):
            err_msg = f"The action {action} is not enabled in config"
            logger.error(err_msg)
            return

        order_id = self.id
        id_shop = self.yuju_shop_id
        id_order = self.channel_order_id
        id_channel_order = self.channel_id

        if not id_order or not id_shop or not id_channel_order:
            err_msg = "Some data are empty, please validate id_shop, id_order, id_channel"
            logger.error(err_msg)
            self.message_post(body=err_msg)
            return
        
        data = {
            "id_shop" : id_shop,
            "id_channel" : 2301,
            "id_order" : id_order,
            "id_channel_order" : id_channel_order,
            "order_id" : order_id,
            "action": action
        }

        logger.info(data)

        url = f"{config.service_url}/order_action"
        
        try:
            requests.post(url, json=data)
        except Exception as e:
            err_msg = f"Ocurrio un error al enviar el mensaje de accion {action}: {e}"
            logger.error()
            self.message_post(body=err_msg)
        else:
            self.message_post(body=f"Se ha enviado webhook de accion {action}")
    
        
    def test_get_invoice_xml(self):
        logger.info("TESTING GET XML")
        for rec in self:
            res = self.get_invoice_xml(rec.id)
            logger.info(res)

    def download_label(self):
        if self.id and self.yuju_url_label:
            return {
                'type': 'ir.actions.act_url',
                'url': f'{self.yuju_url_label}/',
                'target': 'new',
            }

    @api.model
    def update_shipping_url(self, order_id, shipping_url):

        logger.info(f"Update Shipping URL {shipping_url}")

        if not order_id:
            return results.error_result(code='order_id_required',
                                        description='order_id is required')
        
        order = self.search([('id', '=', int(order_id))])

        if not order:
            return results.error_result(code='sale_not_exists',
                                        description='order {} doesn\'t exists'.format(order_id))

        order.ensure_one()

        # config = self.env['madkting.config'].get_config()

        order.write({
            "yuju_url_label" : shipping_url
        })

        order.message_post(body=f"Agrega URL de envio {shipping_url}")

        return results.success_result()

    @api.model
    def print_invoice(self, order_id):

        logger.info("Print Invoice")

        if not order_id:
            return results.error_result(code='order_id_required',
                                        description='order_id is required')
        
        order = self.search([('id', '=', int(order_id))])

        if not order:
            return results.error_result(code='sale_not_exists',
                                        description='order {} doesn\'t exists'.format(order_id))

        order.ensure_one()

        config = self.env['madkting.config'].get_config()

        order.message_post(body="Se intenta generar PDF.")

        if not order.invoice_ids:
            err_msg = 'order {} is not invoiced'.format(order_id)
            order.message_post(body=err_msg)
            return results.error_result(code='sale_not_invoiced',
                                        description=err_msg)

        logger.info("## INTENTA GENERAR PDF ##")
        for invoice in order.invoice_ids:
        
            """ This method is used to generate attachment for pdf report"""
            pdf = self.env['ir.actions.report']._render_qweb_pdf('account.report_invoice', invoice.id)
            if config.invoice_save_pdf_attachment:
                b64_pdf = base64.b64encode(pdf[0])
                # save pdf as attachment
                name = f"{invoice.name}.pdf"
                attachment_id = self.env['ir.attachment'].create({
                    'name': name,
                    'type': 'binary',
                    'datas': b64_pdf,
                    'store_fname': name,
                    'res_model': "account.move",
                    'res_id': invoice.id,
                    'mimetype': 'application/x-pdf'
                })

                logger.info(attachment_id)

        return True

    @api.model
    def get_invoice_xml(self, order_id):

        logger.info("Get factura xml..")
        invoice_data = None

        if not order_id:
            return results.error_result(code='order_id_required',
                                        description='order_id is required')
        
        order = self.search([('id', '=', int(order_id))])

        if not order:
            return results.error_result(code='sale_not_exists',
                                        description='order {} doesn\'t exists'.format(order_id))

        order.ensure_one()

        if not order.invoice_ids:
            err_msg = 'order {} is not invoiced'.format(order_id)
            order.message_post(body=err_msg)
            return results.error_result(code='sale_not_invoiced',
                                        description=err_msg)
        
        config = self.env['madkting.config'].get_config()

        if not config.invoice_prefix_file:
            err_msg = 'Invoice prefix is undefined in config'
            order.message_post(body=err_msg)
            return results.error_result(code='invoice_prefix_file_undefined',
                                        description=err_msg)

        # if not config.invoice_mimetype_file:
        #     err_msg = 'Invoice mimetype is undefined in config'
        #     order.message_post(body=err_msg)
        #     return results.error_result(code='invoice_mimetype_file_undefined',
        #                                 description=err_msg)

        if not config.invoice_country:
            err_msg = 'Invoice Country is undefined in config'
            order.message_post(body=err_msg)
            return results.error_result(code='invoice_country_undefined',
                                        description=err_msg)

        if not config.invoice_currency:
            err_msg = 'Invoice Currency is undefined in config'
            order.message_post(body=err_msg)
            return results.error_result(code='invoice_currency_undefined',
                                        description=err_msg)

        if config.invoice_add_pdf_file:
            self.print_invoice(order.id)

        for invoice in order.invoice_ids:

            if not invoice.state == "posted":
                logger.info("Invoice not posted, continue")
                continue

            if not invoice.attachment_ids:
                err_msg = 'order {} is not invoiced with files attached'.format(order_id)
                order.message_post(body=err_msg)
                return results.error_result(code='sale_not_invoiced_files',
                                        description=err_msg)
            
            if not invoice.partner_id.vat and not config.invoice_partner_vat:
                err_msg = 'order {} invoice partner vat undefined'.format(order_id)
                order.message_post(body=err_msg)
                return results.error_result(code='sale_invoice_partner_vat_undefined',
                                        description=err_msg)

            partner_vat = invoice.partner_id.vat
            if not partner_vat:
                partner_vat = config.invoice_partner_vat

            # Son requeridos!!
            # file_mimetype = config.invoice_mimetype_file
            # file_prefix = config.invoice_prefix_file
            allowed_formats = ["xml"]

            file_prefix = {
                "xml": config.invoice_prefix_file
            }

            file_mimetype = {
                "xml": "application/xml",
            }

            invoice_has = {
                "xml": False
            }

            if config.invoice_add_pdf_file:                
                allowed_formats.append("pdf")
                file_mimetype.update({ 
                    "pdf": "application/pdf"
                })
                file_prefix.update({                
                    "pdf": config.invoice_prefix_pdf_file
                })
                invoice_has.update({                
                    "pdf": False
                })

            attachment_file = None
            attachments = []
            for attach in invoice.attachment_ids:
                logger.info(attach.name)
                logger.info(attach.mimetype)
                file_format = attach.mimetype.split("/")[1]
                
                if file_format not in allowed_formats:
                    logger.info(f"Format {file_format} Not allowed [{allowed_formats}]")
                    continue

                if attach.mimetype == file_mimetype[file_format] and not invoice_has[file_format]:
                    if file_prefix[file_format]:
                        if attach.name.startswith(file_prefix[file_format]):
                            invoice_has[file_format] = True
                            base64_str = attach.datas.decode()
                            attachment_file = base64_str
                            attachments.append({
                                "data": attachment_file,
                                "format": file_format
                            })
                        else:
                            logger.info(f"File {file_format} not start with prefix {file_prefix[file_format]}")
                            continue
                    else:
                        invoice_has[file_format] = True
                        base64_str = attach.datas.decode()
                        attachment_file = base64_str
                        attachments.append({
                            "data": attachment_file,
                            "format": file_format
                        })

            if not attachments:
                logger.error(f"No se encontro archivos adjuntos con prefijo [{file_prefix}], tipo: [{file_mimetype}]")
                err_msg = 'order {} is not invoiced with xml'.format(order_id)
                order.message_post(err_msg)
                return results.error_result(code='sale_not_invoiced_xml',
                                        description=err_msg)

            order.message_post(body="Obtiene datos de la factura")
            
            invoice_data = {
                "attachments" : attachments
            }
            
            separator = config.invoice_separator
            if not separator:
                logger.info("Invoice separator not defined, using default: /")
                separator = " "

            invoice_name = invoice.name
            name_pieces = invoice_name.split(separator)
            
            if len(name_pieces) > 1:
                idx_folio = len(name_pieces) - 1
                folio = name_pieces[idx_folio]
                invoice_data["folio"] = int(folio)

            serie = config.invoice_serie
            if not serie:
                logger.info("Invoice serie not defined, using default: A")
                serie = "A"

            invoice_data["serie"] = serie
            invoice_data["country"] = config.invoice_country
            invoice_data["currency"] = config.invoice_currency
            invoice_data["document_type"] = config.invoice_doc_type
            invoice_data["invoice_date"] = invoice.invoice_date.strftime("%Y-%m-%dT00:00:00")
            invoice_data["name"] = invoice.partner_id.name
            invoice_data["taxid"] = partner_vat
            invoice_data["subtotal"] = invoice.amount_untaxed
            invoice_data["iva"] = invoice.amount_tax
            invoice_data["total"] = invoice.amount_total
            invoice_data["order_ref"] = order.channel_order_reference

            invoice_data["items"] = []

            for line in invoice.invoice_line_ids:
                invoice_data["items"].append({
                    "sku" : line.product_id.default_code
                })

            logger.info(invoice_data)
            break

        return results.success_result(data=invoice_data)

    def _concilia_factura_pago(self, payment, factura):
        credit_line = None
        for line in payment.line_ids:

            if line.credit > 0:
                credit_line = line

        if credit_line:
            invoice_lines = factura.line_ids.filtered(lambda line: line.account_id == credit_line.account_id and not line.reconciled)
            
            if invoice_lines:
                invoice_lines += credit_line
                logger.info(invoice_lines)
                try:
                    rec = invoice_lines.reconcile()
                except Exception as e:
                    post_message = "Failed to reconcile invoice {} with payment {}, error: {}.".format(factura.name, payment.name, e)
                    factura.message_post(body=post_message)
                    return False
                else:
                    if not factura.payment_state == 'paid':
                        post_message = "No se ha pagado la factura {}.".format(factura.name)
                        factura.message_post(body=post_message)
                        return False

                    logger.info("Reconciled")
                    logger.info(rec)
                    return True
        
        post_message = "Failed to reconcile invoice {} with payment {}.".format(factura.name, payment.name)
        factura.message_post(body=post_message)
        return False

    @api.model
    def test_concilia_factura(self, invoice_id, payment_id):
        factura = self.env['account.move'].browse(invoice_id)
        pago = self.env['account.payment'].browse(payment_id)
        return self._concilia_factura_pago(pago, factura)

    @api.model
    def charge_invoice(self, invoice_id, payment_method_id=None, journal_id=None, sale_id=None):
        """
        :param invoice_id:
        :type invoice_id: int
        :param payment_method_id:
        :type payment_method_id: int
        :param journal_id:
        :type journal_id: int
        :return: True on success or False if the invoice is already charged
        :rtype: bool
        """
        sale = False 
        if sale_id:
            invoice = False
            sale = self.env['sale.order'].search([('id', '=', int(sale_id))], limit=1)
            if sale and sale.payment_id:
                return results.success_result()
                # return results.error_result(code='already_paid',
                #                             description='sale order already paid')
        else:
            invoice = self.env['account.move'].search([('id', '=', invoice_id)])

            if not invoice:
                return results.error_result(code='invoice_not_exists',
                                            description='invoice doesn\'t exists')
            invoice.ensure_one()

            # Update invoice_payment_state instead state on Odoo V13
            if invoice.payment_state == 'paid':
                return results.error_result(code='already_paid',
                                            description='invoice already paid')

        payment_model = self.env['account.payment']

        if not payment_method_id:
            payment_method = self.env['account.payment.method'] \
                                 .search([('payment_type', '=', 'inbound'),
                                          '|', ('code', '=', 'manual'),
                                               ('code', '=', 'electronic')])
            if len(payment_method) >= 1:
                payment_method_id = payment_method.sorted(lambda method: method.id)[0].id
            else:
                return results.error_result(
                    code='not_payment_method',
                    description='payment_method_id must be specified or at '
                                'least you must have one method type inbound '
                                'with code manual or electronic'
                )

        if not journal_id:
            if sale:
                journal = self.env['account.journal'] \
                            .search([('company_id', '=', sale.company_id.id),
                                    ('active', '=', True),
                                    ('type', '=', 'bank')])
            else:
                journal = self.env['account.journal'] \
                            .search([('company_id', '=', invoice.company_id.id),
                                    ('active', '=', True),
                                    ('type', '=', 'bank')])
            if len(journal) >= 1:
                journal_id = journal.sorted(lambda j: j.id)[0].id
            else:
                return results.error_result(
                    code='not_account_journal',
                    description='journal_id must be specified or at least you '
                                'must have one account_journal active in your '
                                'company of type bank'
                )
        try:

            if sale:
                payment = payment_model.create({'amount': sale.amount_total,
                                                'partner_id' : sale.partner_id.id,
                                                'ref' : sale.name,
                                                'date': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                                                'payment_type': 'inbound',
                                                'payment_method_id': payment_method_id,
                                                'journal_id': journal_id,
                                                'currency_id': sale.pricelist_id and sale.pricelist_id.currency_id.id,
                                                'partner_type': 'customer'})                
            else:
                payment = payment_model.create({'amount': invoice.amount_total,
                                                'partner_id' : invoice.partner_id.id,
                                                'ref' : invoice.invoice_origin,
                                                'date': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                                                'payment_type': 'inbound',
                                                'payment_method_id': payment_method_id,
                                                'journal_id': journal_id,
                                                'currency_id': invoice.currency_id.id,
                                                'partner_type': 'customer'})
                # payment.invoice_ids = [invoice_id]
        
        except exceptions.AccessError as err:
            return results.error_result(
                code='access_error',
                description=str(err)
            )
        except Exception as ex:
            logger.exception(ex)
            return results.error_result(
                code='invoice_payment_error',
                description='payment for invoice couldn\'t be saved because '
                            'of the following exception: {}'.format(ex))

        try:
            payment.action_post()
        except exceptions.AccessError as err:
            return results.error_result(
                code='access_error',
                description=str(err)
            )
        except Exception as ex:
            logger.exception(ex)
            return results.error_result(
                code='payment_post_error',
                description='Payment {} couldn\'t be posted because of the '
                            'following error: {}'.format(payment.id, ex)
            )

        if sale:
            try:           
                sale.payment_id = payment.id
            except exceptions.AccessError as err:
                return results.error_result(
                    code='access_error',
                    description=str(err)
                )
            except Exception as ex:
                logger.exception(ex)
                return results.error_result(
                    code='invoice_update_payed',
                    description='Error updating invoice to payed: {}'.format(ex)
                )
            else:
                return results.success_result()
           
        else:
            try:               
                self._concilia_factura_pago(payment, invoice)
            except Exception as ex:
                logger.exception(ex)
                post_message = "Error al pagar la factura: {}.".format(ex)
                invoice.message_post(body=post_message)
                return results.error_result(
                    code='invoice_update_payed',
                    description='Error updating invoice to payed: {}'.format(ex)
                )
            else:
                return results.success_result()

    @api.model
    def cancel_order(self, order_id):
        """
        :param order_id:
        :type order_id: int
        :return: results dictionary
        :rtype: dict
        """
        config = self.env['madkting.config'].get_config()
        sale_order = self.search([('id', '=', order_id)])
        warnings = list()

        if not sale_order:
            return results.error_result(code='sale_not_exists')

        if sale_order.state == 'cancel':
            return results.error_result(code='sale_already_cancelled')

        # validate if the sale lines moves are not done
        # if sale_order.has_lines_not_cancellable():
        #     return results.error_result(
        #         code='sale_stock_move_done',
        #         description='The sale has stock moves with status done'
        #     )

        try:
            force_cancel = config.orders_force_cancel
            sale_order.with_context({'disable_cancel_warning': force_cancel}).action_cancel()
        except exceptions.AccessError as err:
            post_message = "Error trying to cancel order {}.".format(err)
            logger.debug(post_message)
            sale_order.message_post(body=post_message)
            return results.error_result(
                code='access_error',
                description=str(err)
            )
        except Exception as ex:
            post_message = "Error trying to cancel order {}.".format(err)
            logger.debug(post_message)
            sale_order.message_post(body=post_message)
            return results.error_result(
                code='cancel_error',
                description=str(ex)
            )
        else:
            if sale_order.state == 'cancel':
                post_message = 'Order cancelled'
                logger.debug(post_message)
                sale_order.message_post(body=post_message)

                if sale_order.invoice_ids:                
                    try:
                        sale_order.invoice_ids.button_draft()
                        sale_order.invoice_ids.unlink()
                    except Exception as ex:
                        post_message = 'invoice couldn\'t be cancelled: {}'.format(ex)
                        logger.debug(post_message)
                        sale_order.message_post(body=post_message)
                        warnings.append(post_message)
                    else:
                        post_message = 'Invoice cancelled'
                        logger.debug(post_message)
                        sale_order.message_post(body=post_message)
            else:
                post_message = f'No se puede cancelar la orden {sale_order.name}, verifique si tiene transacciones realizadas'
                logger.warning(post_message)
                warnings.append(post_message)
                sale_order.message_post(body=post_message)

            return results.success_result(data=False, warnings=warnings)

    def _validate_order_fields(self, order_data):
        """
        :param order_data:
        :type order_data: dict
        :return: list of errors
        :rtype: list
        """
        errors = list()
        order_fields = {
            'company_id': int,
            'date_order': str,
            'validity_date': str,
            # 'confirmation_date': str, # deprecated
            'note': str,
            'partner_id': int,
            'require_signature': bool,
            'require_payment': bool,
            'pricelist_id': int,
            'invoice_status': str,
            'payment_term_id': int,
            # 'team_id': int,
            'warehouse_id': int,
            'picking_policy': str,
            'channel': str,  # madkting
            'channel_id': int,  # madkting
            'channel_order_reference': str,  # madkting
            'channel_order_id': str,  # madkting
            'lines': list
        }
        for field, type_ in order_fields.items():
            if field not in order_data:
                errors.append('missing required field {}'.format(field))
                continue
            if not isinstance(order_data[field], type_):
                errors.append('field {} must be instance of {}'.format(field, type_))
        if errors:
            return errors

    def has_lines_not_cancellable(self):
        """
        :return:
        :rtype: bool
        """
        self.ensure_one()
        for line in self.order_line:
            if any(move.state == 'done' for move in line.move_ids):
                return True
        return False

    def has_journal_not_cancellable(self):
        """
        :return:
        :type: bool
        """
        self.ensure_one()
        invoice = self.invoice_ids
        invoice.ensure_one()
        for move in invoice.move_id:
            if any(not journal.update_posted for journal in move.journal_id):
                return True
        return False
