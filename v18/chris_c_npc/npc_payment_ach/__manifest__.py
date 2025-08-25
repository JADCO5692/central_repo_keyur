# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
    'name': "NP Collaborator ACH Payment Customizations",
    'version': '18.0.1.0',
    'category': 'CRM',
    'summary': "Customizations for the ACH payment method",
    'description': """
This module currently does the ff:\n
1) Set invoice to 'In Payment' payment state when an ACH Debit is initiated.
    """,
    'author': "Mark Dela Cruz",
    'website': 'https://www.markdelacruz.com',
    'depends': [
        'base',
        'account',
        'payment',
    ],
    'data': [
        # 'data/ir_config_parameter_data.xml',
        # 'views/crm_views.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': False,
    'assets': {
        'web.assets_backend': [
        ],
    },
    'license': 'LGPL-3',
}
