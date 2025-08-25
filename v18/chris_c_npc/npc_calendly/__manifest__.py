# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
    'name': "NP Calendly Integration",
    'version': '18.0.1.2',
    'category': 'CRM',
    'summary': "Add Calendly Schedule on CRM",
    'description': """
This module currently does the ff:\n
1) Convert leads to opportunities and adds their Calendly Schedule
    """,
    'author': "Mark Dela Cruz",
    'website': 'https://www.markdelacruz.com',
    'depends': [
        'base',
        'crm',
        'npc_crm',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'wizard/sync_views.xml',
        'views/res_config_views.xml',
        'views/crm_views.xml',
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
