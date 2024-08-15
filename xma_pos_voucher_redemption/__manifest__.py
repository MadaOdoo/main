# -*- coding: utf-8 -*-
{
    'name': "Canjeo de vales en punto de venta",
    'summary': """
    """,
    'description': """
    """,
    'author': "Xmarts",
    'contributors': "joseluis.vences@xmarts.com",
    'website': "http://www.xmarts.com",
    'category': 'Point Of Sale',
    'version': '16.0.1.0.0',
    'depends': ['base','point_of_sale', 'account'],
    'data': [
        'data/sequence.xml',
        'security/ir.model.access.csv',
        'views/control_vales_views.xml',
        'views/inherit_account_journal_views.xml',
        'views/inherit_account_payment_views.xml',
        'views/inherit_pos_order_views.xml',
        'views/inherit_res_partner_views.xml',
        'views/pos_config_views.xml',
        'views/pos_payment_method_view.xml',
        'reports/report.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'xma_pos_voucher_redemption/static/src/css/modal_dialog.css',
            'xma_pos_voucher_redemption/static/src/js/**/*.js',
            'xma_pos_voucher_redemption/static/src/xml/**/*',
        ],
    }
}
