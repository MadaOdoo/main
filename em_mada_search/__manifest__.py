# -*- coding: utf-8 -*-
{
    'name': "MADA - Search Extension Module",
    'summary': "MADA - Search Extension Module",
    'description': """ Show the product image in the search engine """,
    'author': "Alfonso Gonzalez",
    'website': "https://ntropy.tech/odoo",
    'category': 'Customizations',
    'version': '0.1',
    'license': "AGPL-3",
    'depends': ['base',
                'product'],
    'data': [
        'views/product_template_tree_view.xml',
    ],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
