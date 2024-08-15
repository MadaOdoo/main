# -*- coding: utf-8 -*-
{
    'name': "Facturas y Notas de Credito por Distribuidora",
    'summary': """
    """,
    'description': """
    """,
    'author': "Xmarts",
    'contributors': "daniela.roche@xmarts.com",
    'website': "http://www.xmarts.com",
    'category': 'Point Of Sale',
    'version': '16.0.1.0.0',
    'depends': ['base', 'auth_totp', 'xma_pos_voucher_redemption', 'l10n_mx_pos_global_invoice', 'product_unspsc'],
    'data': [
        'data/data_product_product.xml',
        'data/data_ir_cron.xml',
        'security/ir.model.access.csv',
        'views/inherit_res_config_settings_views.xml',
        'views/inherit_pos_config_views.xml',
        'views/inherit_res_users_views.xml',
        'views/inherit_account_move_views.xml',
        'views/inherit_account_payment_views.xml',
        'views/inherit_pos_order_views.xml',
        'views/voucher_report_views.xml',
        'views/inherit_pos_payment_views.xml',
    ],
}
