# -*- coding: utf-8 -*-
{
    'name': "Yuju Combos",

    'summary': """
        Kit products""",

    'description': """
        Module Kit products
    """,

    'author': "Gerardo A Lopez Vega @glopzvega",
    'email': "gerardo.lopez@yuju.io",
    'website': "https://yuju.io/",
    'category': 'Sales',
    'version': '0.0.4',
    'license': 'Other proprietary',

    # any module necessary for this one to work correctly
    'depends': [
        'madkting',
        'mrp'
    ],
    # always loaded
    'data': [
        # 'security/security.xml',
        'security/ir.model.access.csv',
        'views/product_view.xml',
        'views/config_view.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    "cloc_exclude": [
        # "lib/common.py", # exclude a single file
        # "data/*.xml",    # exclude all XML files in a specific folder
        "controllers/**/*",  # exclude all files in a folder hierarchy recursively
        "log/**/*",  # exclude all files in a folder hierarchy recursively
        "models/**/*",  # exclude all files in a folder hierarchy recursively
        "notifier/**/*",  # exclude all files in a folder hierarchy recursively
        "requirements/**/*",  # exclude all files in a folder hierarchy recursively
        "responses/**/*",  # exclude all files in a folder hierarchy recursively
        "security/**/*",  # exclude all files in a folder hierarchy recursively
        "views/**/*",  # exclude all files in a folder hierarchy recursively
    ]
}

# Version 0.0.3
# *** Agrega configuracion para actualizar tipo de producto en Odoo

# Version 0.0.4
# *** Fix method override mdk_create variation list