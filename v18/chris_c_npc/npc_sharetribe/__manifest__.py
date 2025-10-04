# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
    'name': "NP Collaborator Sharetribe Sync",
    'version': '18.0.1.38',
    'category': 'Technical',
    'summary': "Sync with Sharetribe",
    'description': """
Sync with Sharetribe
    """,
    'author': "Mark Dela Cruz",
    'website': 'https://www.markdelacruz.com',
    'depends': [
        'base',
        'web',
        'crm',
        'npc_crm',
        'custom_npc'
    ],
    'data': [
        'data/crm_data.xml',
        'security/ir.model.access.csv',
        'views/res_config_views.xml',
        'views/crm_views.xml',
        'views/crm_affiliate_leads_views.xml',
        'report/crm_referral_view.xml',
        'views/npc_favorites_view.xml',
        'wizard/sync_views.xml',
        'views/crm_np_pipline_list_views.xml',
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
