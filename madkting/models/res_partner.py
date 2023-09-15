# -*- coding: utf-8 -*-
# File:           res_partner.py
# Author:         Israel Calderón
# Copyright:      (C) 2019 All rights reserved by Madkting
# Created:        2019-03-20
from odoo import models, fields, api
from odoo import exceptions
from ..responses import results
from ..log.logger import logger

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create_customer(self, customer_data):
        """
        :type customer_data: dict
        :param customer_data: dictionary with customer data
        {
            'name': str,
            'tz': str, #'America/Mexico_City',
            'vat': str, # tax_id
            'comment': str,
            'function': str,
            'street': str,
            'street2': str,
            'zip': str,
            'city': str,
            'country_code': str, # MX
            'email': str,
            'phone': str,
            'mobile': str,
            'company_id': int,
            'company_name': str
            'billing_address': {
                'name': str,
                'tz': str, #'America/Mexico_City',
                'vat': str, # tax_id
                'comment': str,
                'function': str,
                'street': str,
                'street2': str,
                'zip': str,
                'city': str,
                'country_code': str,
                'email': str,
                'phone': str,
                'mobile': str,
                'company_id': int,
                'company_name': str
            },
            'shipping_address': {
                'name': str,
                'tz': str, #'America/Mexico_City',
                'vat': str, # tax_id
                'comment': str,
                'function': str,
                'street': str,
                'street2': str,
                'zip': str,
                'city': str,
                'country_code': str,
                'email': str,
                'phone': str,
                'mobile': str,
                'company_id': int,
                'company_name': str
            }
        }
        :return:
        """
        config = self.env['madkting.config'].get_config()

        defaults = {
            'active': True,
            'customer_rank': 1,
            'employee': False,
            'is_company': False,
            'industry_id': False,
            'color': 0
        }
        customer_data.update(defaults)
        partners = {
            'delivery': customer_data.pop('billing_address', dict()),
            'invoice': customer_data.pop('shipping_address', dict())
        }

        if hasattr(self, 'partner_gid'):
            defaults['partner_gid'] = 0

        if not hasattr(self, 'l10n_mx_edi_colony'):
            city_name = customer_data.pop('l10n_mx_edi_colony', None)
            if hasattr(self, 'city_id'):
                customer_data["city_id"] = self._get_city_id(city_name)
        
        if not hasattr(self, 'l10n_mx_edi_locality'):
            state_name = customer_data.pop('l10n_mx_edi_locality', None)
            customer_data["state_id"] = self._get_state_id(state_name)

        customer_data = self.update_mapping_fields(customer_data)

        logger.debug(customer_data)

        partner_exist = False
        partner_found = None
        if config.validate_partner_exists and customer_data.get('vat'):
            vat_id = customer_data.get('vat')
            partner_found = self.search([('vat', '=', vat_id)], limit=1)
            if partner_found.id:
                partner_exist = True
        
        if partner_exist:
            new_customer = partner_found
        else:
            try:
                country_code = customer_data.pop('country_code', None)
                customer_data['country_id'] = self._get_country_id(country_code)
                logger.info("## CUSTOMER DATA ##")
                logger.info(customer_data)
                new_customer = self.create(customer_data)
            except exceptions.AccessError as err:
                return results.error_result(
                    code='access_error',
                    description=str(err)
                )
            except Exception as ex:
                return results.error_result(
                    code='create_costumer_error',
                    description='Error trying to create new costumer: {}'.format(ex)
                )
        warnings = list()
        for type_, partner in partners.items():
            if not partner:
                continue
            r = self.add_address(customer_id=new_customer.id,
                                 type_=type_,
                                 address=partner)

            if not r['success']:
                warnings.extend(r['errors'])
        remove_fields = ['image', 'image_medium', 'image_small', 'image_1920',
                         'image_1024', 'image_512', 'image_256', 'image_128']
        new_customer_data = new_customer.copy_data()[0]
        new_customer_data['id'] = new_customer.id
        for field in remove_fields:
            new_customer_data.pop(field, None)
        return results.success_result(data=new_customer_data, warnings=warnings)

    @api.model
    def update_mapping_fields(self, customer_data):
        logger.debug("MAIN UPDATE MAPPING")
        customer_data = self.env['yuju.mapping.field'].update_mapping_fields(customer_data, 'res.partner')
        return customer_data

    @api.model
    def add_address(self, customer_id, type_, address):
        """
        :param customer_id:
        :type customer_id:int
        :param type_: delivery or invoice
        :type type_: str
        :param address:
        :type address: dict
        :return:
        """
        parent_customer = self.browse(customer_id)
        country_code = address.pop('country_code', None)

        if not hasattr(self, 'l10n_mx_edi_colony'):
            city_name = address.pop('l10n_mx_edi_colony', None)
            if hasattr(self, 'city_id'):
                address["city_id"] = self._get_city_id(city_name)
        
        if not hasattr(self, 'l10n_mx_edi_locality'):
            state_name = address.pop('l10n_mx_edi_locality', None)
            address["state_id"] = self._get_state_id(state_name)
        
        defaults = {
            'active': True,
            'customer_rank': 1,
            'employee': False,
            'is_company': False,
            'industry_id': False,
            'color': 0,
            'type': type_,
            'parent_id': customer_id,
            'country_id': self._get_country_id(country_code)
        }

        if not defaults['country_id']:
            defaults['country_id'] = parent_customer.country_id.id

        if hasattr(self, 'partner_gid'):
            defaults['partner_gid'] = 0

        address.update(defaults)

        address = self.update_mapping_fields(address)

        try:
            new_address = self.create(address)
        except exceptions.AccessError as err:
            return results.error_result(
                code='access_error',
                description=str(err)
            )
        except Exception as ex:
            return results.error_result(
                code='create_costumer_error',
                description='Error trying to create new costumer address: {}'.format(ex)
            )
        else:
            data = {'id': new_address.id}
            return results.success_result(data=data)

    def _get_city_id(self, city_name):
        """
        :param city_name:
        :type city_name: str
        :return: int | None
        """
        city = self.env['res.city'].search([('name', 'ilike', city_name)])
        if not city:
            return
        elif len(city) != 1:
            return
        else:
            return city.id

    def _get_state_id(self, state_name):
        """
        :param state_name:
        :type state_name: str
        :return: int | None
        """
        state = self.env['res.country.state'].search([('name', 'ilike', state_name)])
        if not state:
            return
        elif len(state) != 1:
            return
        else:
            return state.id

    def _get_country_id(self, country_code):
        """
        :param country_code:
        :type country_code: str
        :return: int | None
        """
        logger.info("## BUSCA PAIS ##")
        logger.info(country_code)
        country = self.env['res.country'].search([('code', '=', country_code)])
        logger.info(country)
        if not country:
            return
        elif len(country) != 1:
            return
        else:
            return country.id
