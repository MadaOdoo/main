# -*- coding: utf-8 -*-
# File:           res_partner.py
# Author:         Israel Calderón
# Copyright:      (C) 2019 All rights reserved by Madkting
# Created:        2019-03-20
# from odoo import models, api
# from datetime import datetime
#
#
# class Picking(models.Model):
#     _inherit = 'stock.picking'
#
#     @api.model
#     def product_stock_receipt(self, product_id, product_name, company_id,
#                               location_id, location_dest_id, quantity, partner_id=None):
#         """
#         TODO: implement initial stock functionality in this method
#         """
#         if not partner_id:
#             partner_id = self._uid
#
#         picking = {
#             'origin': False,
#             'note': False,
#             'move_type': 'direct',
#             'date': datetime.now(),
#             'location_id': location_id,
#             'location_dest_id': location_dest_id,
#             'move_lines': [(0, 0,
#                             {'state': 'draft',
#                              'name': product_name,
#                              'sequence': 10,
#                              'priority': False,
#                              'date': datetime.now(),
#                              'company_id': company_id,
#                              'date_expected': datetime.now(),
#                              'product_id': product_id,
#                              'product_uom_qty': quantity,
#                              'product_uom': 1,
#                              'product_packaging': False,
#                              'location_id': location_id,
#                              'location_dest_id': location_dest_id,
#                              'partner_id': False,
#                              'note': False,
#                              'origin': False,
#                              'procure_method': 'make_to_stock',
#                              'group_id': False,
#                              'rule_id': False,
#                              'propagate': True,
#                              'picking_type_id': 1,
#                              'inventory_id': False,
#                              'restrict_partner_id': False,
#                              'route_ids': [(6, 0, [])],
#                              'warehouse_id': False,
#                              'additional': False,
#                              'package_level_id': False,
#                              'sale_line_id': False}
#                             )],
#             'picking_type_id': 1, # TODO
#             'partner_id': 67, # TODO
#             'company_id': company_id,
#             'owner_id': False,
#             'printed': False,
#             'is_locked': True,
#             'immediate_transfer': False,
#             'message_main_attachment_id': False
#         }
