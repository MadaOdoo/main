from odoo.addons.component.core import Component
from ..log.logger import logger
from ..log.logger import logs
from ..notifier import notifier

class MadktingStockMoveListener(Component):
    _name = 'madkting.stock.move.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['stock.move']

    def on_record_create(self, record, fields=None):
        """
        :param record:
        :param fields:
        :return:
        """
        self.__send_stock_webhook(record)

    def on_record_write(self, record, fields=None):
        """
        :param record:
        :param fields:
        :return:
        """
        self.__send_stock_webhook(record)

    def on_record_unlink(self, record):
        """
        :param record:
        :return:
        """
        self.__send_stock_webhook(record)

    def __send_stock_webhook(self, record):
        """
        :param record:
        :return:
        """
        # logger.info("## LISTENER ##")
        config = self.env['madkting.config'].sudo().get_config()

        if not config or not config.webhook_stock_enabled:
            return

        record_state = getattr(record, 'state', None)

        if record_state in ['assigned', 'done'] and record.product_id.id_product_madkting:            
            # logger.info("##LISTENER ENVIA MSJ##")
            try:
                notifier.send_stock_webhook(self.env, record.product_id, record.company_id.id)
            except Exception as ex:
                logger.exception(ex)
        
# https://apps.yuju.io/api/sales/in/2301?id_shop=1085876
