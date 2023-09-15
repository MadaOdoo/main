# -*- coding: utf-8 -*-
# File:           res_partner.py
# Author:         Israel Calderón
# Copyright:      (C) 2019 All rights reserved by Madkting
# Created:        2019-07-15
from odoo import models, api


class UoM(models.Model):
    _inherit = 'uom.uom'

    @api.model
    def get_uom_by_name(self, name):
        """
        Retrieves uom based on name and type. Only works with kg (weight) and cm (size)
        :param name: only accept kg and cm
        :type name: str
        :return: Unit of measure model
        """
        uom_name = name.lower()
        measure_types = {'kg': 'weight', 'cm': 'length'}
        if uom_name not in measure_types:
            raise ValueError(
                'invalid uom {}, madkting only work with kg and cm'.format(uom_name)
            )
        return self.search([('name', '=', name),
                            ('measure_type', '=', measure_types[name]),
                            ('active', '=', True)],
                           limit=1)
