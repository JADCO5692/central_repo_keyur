# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
    'name': "NP Collaborator Sharetribe and Memberstack Sync",
    'version': '18.0.1.0',
    'category': 'CRM',
    'summary': "Sync with Sharetribe and Memberstack",
    'description': """
This module currently does two things:\n
1. Run Sharetribe and Memberstack sync as a cron job
2. Merge Sharetribe and Memberstack after sync if any of the PHYS npc_user_type are the same
    """,
    'website': 'https://www.npcollaborator.com',
    'depends': [
        'base',
        'crm',
        'npc_crm',
        'npc_memberstack',
        'npc_sharetribe',
    ],
    'data': [
        'data/ir_cron_data.xml',
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
