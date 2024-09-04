{
    'name': 'Flujo de Patrones de Pedido para Ventas',
    'version': '16.0.0.1',
    'category': '',
    'license': 'AGPL-3',
    'summary': "Flujo de Patrones de Pedido para Ventas",
    'author': "Franco Najarro",
    'website': '',
    'depends': ['base','sale','stock','uom','contacts','product_matrix','sale_product_matrix'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_view.xml',
        'views/sale_order_view.xml',
        'views/product_matrix_templates.xml',
        'reports/report_sale_order_patron.xml',
        #'reports/sale_order_report.xml',
        #'reports/ir_actions_report.xml',
        ],
    'assets':{
        'web.assets_backend':[
            'sale_order_patron_pedido/static/src/js/sale_product_field.js',
            'sale_order_patron_pedido/static/src/xml/**/*',
        ],
    },
    'installable': True,
}