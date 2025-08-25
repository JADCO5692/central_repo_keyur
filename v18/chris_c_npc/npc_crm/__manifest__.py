# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
    'name': "NP Collaborator CRM Customizations",
    'version': '18.0.1.9',
    'category': 'CRM',
    'summary': "Customizations for NP Collaborator CRM",
    'description': """
Customizations for NP Collaborator CRM
    """,
    'author': "Mark Dela Cruz",
    'website': 'https://www.markdelacruz.com',
    'depends': [
        'base',
        'web',
        'crm',
        'sales_team',
        'sign',
    ],
    'data': [
        'data/crm_team_data.xml',
        'data/practice_type_data.xml',
        'data/physician_server_action_data.xml',
        'security/ir.model.access.csv',
        'views/partner_views.xml',
        'views/crm_views.xml',
        'views/sign_view.xml',
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
