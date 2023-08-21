# -*- coding: utf-8 -*-
{
    'name': 'Mada Product Import',
    'version': '0.0.2',
    'category': 'sale',
    'description': """
    Mara Product Import
    """,
    'author': 'gsisa.asilva@gmail.com',
    'depends': [
        'sale',
        'stock',
        'purchase',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/mada_product_import.xml',
    ],
    'test': [],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
