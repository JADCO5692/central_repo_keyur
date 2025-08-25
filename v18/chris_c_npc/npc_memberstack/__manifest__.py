# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
    'name': "NP Collaborator Memberstack Sync",
    'version': '18.0.1.0',
    'category': 'Technical',
    'summary': "Sync with Memberstack",
    'description': """
Sync with Memberstack
    """,
    'author': "Mark Dela Cruz",
    'website': 'https://www.markdelacruz.com',
    'depends': [
        'base',
        'web',
        'crm',
        'npc_crm',
    ],
    'data': [
        # 'data/ir_config_parameter_data.xml',
        'data/crm_tag_data.xml',
        'security/ir.model.access.csv',
        'views/res_config_views.xml',
        'views/crm_views.xml',
        'wizard/sync_views.xml',
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
