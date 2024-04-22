# -*- coding: utf-8 -*-
{
    'name': 'Mada Product Import',
    'version': '0.0.2',
    'category': 'sale',
    'description': """
    Mada Product Import
    """,
    'author': 'gsisa.asilva@gmail.com',
    'license': "LGPL-3",
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
