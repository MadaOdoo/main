from odoo.api import Environment
from ..log.logger import logger
from ..log.logger import logs
import requests
import json

def send_stock_webhook(env, product, company_id, hook_id=None):
    """
    TODO: register webhook failures in order to implement "retries"
    :param env:
    :type env: Environment
    :param product_id:
    :type product_id: int
    :param hook_id:
    :type hook_id: int
    :return:
    """
    logger.debug('### SEND STOCK WEBHOOK ###')
    product_id = product.id
    logger.debug("Producto: {}".format(product_id))
    # if not product.company_id:
    #     company_id = env.user.company_id.id
    # else:
    #     company_id = product.company_id.id
    logger.debug("Company: {}".format(company_id))
    # product = env['product.product'].search([('id', '=', product_id)], limit=1)
    config = env['madkting.config'].sudo().get_config()
        
    ubicaciones_stock = {}

    if config.dropship_enabled and not config.dropship_webhook_enabled:
        logger.debug("### NO STOCK ON DROPSHIP WEBHOOK DISABLED ###")
        return

    if config.stock_source_multi:

        location_ids = config.stock_source_multi.split(',')

        if config.stock_source_channels:
            location_ids += config.stock_source_channels.split(',')
            location_ids = list(set(location_ids))
            logger.debug(f"Locations Channels {location_ids}")

        for location_id in location_ids:
            location = env['stock.location'].search([('id', '=', int(location_id))], limit=1)
            if location.id:
                if config and config.stock_quant_available_quantity_enabled:
                    qty_in_branch = product.with_context({'location' : location.id}).free_qty
                else:
                    qty_in_branch = product.with_context({'location' : location.id}).qty_available
                # qty_in_branch = env['stock.quant']._get_available_quantity(product, location)
                ubicaciones_stock.update({location.id : qty_in_branch})

    else:
        for branch_id, stock in product.get_stock_by_location().items():
            location = env['stock.location'].search([('id', '=', int(branch_id))], limit=1)
            # qty_in_branch = env['stock.quant']._get_available_quantity(product, location)
            if config and config.stock_quant_available_quantity_enabled:
                qty_in_branch = product.with_context({'location' : location.id}).free_qty
            else:
                qty_in_branch = product.with_context({'location' : location.id}).qty_available
            ubicaciones_stock.update({branch_id : qty_in_branch})
    # else:
    #     ubicaciones_stock = product.get_stock_by_location()

    mapping_ids = env['yuju.mapping'].sudo().get_mapping(company_id)
    if mapping_ids:
        # Tiene multi shop activo
        product_mapping_ids = env['yuju.mapping.product'].get_product_mapping_by_product(product_id=product_id, only_active=True)

        if not product_mapping_ids:
            logger.exception('No se encontro mapeo de producto para ID {}'.format(product_id))
            return

        for product_mapping in product_mapping_ids:

            webhook_body = {
                'product_id': product.id,
                'default_code': product.default_code,
                'id_product_madkting': product_mapping.id_product_yuju,
                'event': 'stock_update',
                'qty_available': product.qty_available,
                'quantities' : ubicaciones_stock
                # 'quantities': product.get_stock_by_location()
            }
            data = json.dumps(webhook_body)
            headers = {'Content-Type': 'application/json'}

            webhook_suscriptions = env['madkting.webhook'].search([
                ('hook_type', '=', 'stock'),
                ('active', '=', True),
                ('company_id', '=', company_id),
                ('url', 'ilike', product_mapping.id_shop_yuju),
            ], limit=1)

            for webhook in webhook_suscriptions:
                """
                TODO: if the webhook fails store it into a database for retry implementation
                """
                success = send_webhook(env, webhook.url, data, headers)

    else:
        if hook_id:
            webhook_suscriptions = env['madkting.webhook'].search([('id', '=', hook_id)])
        else:
            webhook_suscriptions = env['madkting.webhook'].search([
                ('hook_type', '=', 'stock'),
                ('active', '=', True),
                ('company_id', '=', company_id)
            ])

        webhook_body = {
            'product_id': product.id,
            'default_code': product.default_code,
            'id_product_madkting': product.id_product_madkting,
            'event': 'stock_update',
            'qty_available': product.qty_available,
            'quantities' : ubicaciones_stock
            # 'quantities': product.get_stock_by_location()
        }
        data = json.dumps(webhook_body)
        headers = {'Content-Type': 'application/json'}
        for webhook in webhook_suscriptions:
            """
            TODO: if the webhook fails store it into a database for retry implementation
            """
            success = send_webhook(env, webhook.url, data, headers)

def send_webhook(env, url, data, headers):
    """
    :param url:
    :param data:
    :param headers:
    :return:
    """
    config = env['madkting.config'].sudo().get_config()
    logs("#### SEND WEBHOOK ####", config)
    logs(data, config)
    logs(url, config)
    logs(headers, config)
    try:
        response = requests.post(url, data=data, headers=headers)
    except Exception as ex:
        logger.exception(ex)
        return False
    else:
        if not response.ok:
            logger.error(response.text)
            return False
        return True
