# -*- coding: utf-8 -*-
{
    'name': "MADA - Extension Module",

    'summary': """MADA - Extension Module""",

    'description': """MADA - Extension Module""",
    'author': "Alfonso Gonzalez",
    'website': "https://ntropy.tech",
    'category': 'Customizations',
    'version': '15.0.0.0.8',
    'license': "AGPL-3",
    'sequence': "-90",
    'depends': [
        'base'
    ],

    'data': [
        # Security
        #'security/ir.model.access.csv',
        # Wizard
        # Views
        'views/account.move.xml',
        # Data Sample
    ],
    'images': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
