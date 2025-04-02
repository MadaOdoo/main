# -*- coding: utf-8 -*-
{
    'name': "MADA - Extension Module",

    'summary': """MADA - Extension Module""",

    'description': """MADA - Extension Module""",
    'author': "Alfonso Gonzalez",
    'website': "https://ntropy.tech/odoo",
    'category': 'Customizations',
    'version': '18.0.1.0',
    'license': "AGPL-3",
    'sequence': "-90",
    'depends': [
        'sale_management',
        'account_accountant'
    ],
    'data': [
        # Security
        # Wizard
        # Views
        'views/account.move.xml'
        # Data Sample
    ],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
