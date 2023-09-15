# -*- coding: utf-8 -*-
# File:           res_partner.py
# Author:         Israel Calderón
# Copyright:      (C) 2019 All rights reserved by Madkting
# Created:        2019-08-01

from odoo import models, api

from ..log.logger import logger


class Base(models.AbstractModel):
    # events notifiers
    _inherit = 'base'

    @api.model_create_multi
    def create(self, vals_list):
        record_ids = super(Base, self).create(vals_list)
        idx = 0
        for record in record_ids:
            try:
                self._event('on_record_create').notify(record, fields=vals_list[idx].keys())
            except Exception as ex:
                logger.exception(ex)
            else:
                idx += 1
        return record_ids

    def write(self, vals):
        record = super(Base, self).write(vals)
        try:
            self._event('on_record_write').notify(record, fields=vals.keys())
        except Exception as ex:
            logger.exception(ex)
        return record
