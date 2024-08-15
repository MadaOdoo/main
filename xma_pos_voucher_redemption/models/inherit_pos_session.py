# -*- coding: utf-8 -*-

from odoo import models

class InheritPosSession(models.Model):
    _inherit = 'pos.session'

    def _pos_data_process(self, loaded_data):
        super()._pos_data_process(loaded_data)
        loaded_data['journal_by_id'] = {journal['id']: journal for journal in loaded_data['account.journal']}

    def _pos_ui_models_to_load(self):
        result = super()._pos_ui_models_to_load()
        new_model = 'account.journal'
        if new_model not in result:
            result.append(new_model)
        return result

    def _loader_params_account_journal(self):
        return {'search_params': {'domain': [], 'fields': ['name', 'is_vale']}}

    def _get_pos_ui_account_journal(self, params):
        return self.env['account.journal'].search_read(**params['search_params'])

    def _loader_params_pos_payment_method(self):
        result = super()._loader_params_pos_payment_method()
        result['search_params']['fields'].append('journal_id')
        result['search_params']['fields'].append('is_bank_terminal')
        return result

    def _loader_params_res_partner(self):
        result = super()._loader_params_res_partner()
        result['search_params']['fields'].append('curp')
        return result

    def _create_split_account_payment(self, payment, amounts):
        result = super()._create_split_account_payment(payment, amounts)
        pos_order_id = payment.pos_order_id
        result.payment_id.folio_vale = pos_order_id.folio_vale
        result.payment_id.state_vale = pos_order_id.state_vale
        result.payment_id.pos_vale_order_id = pos_order_id
        payment.pos_order_id.limpiar_registro_vale(pos_order_id.folio_vale)
        return result
