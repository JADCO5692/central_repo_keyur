# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
    'name': "NP Collaborator Twilio SMS Customizations",
    'version': '18.0.1.1',
    'category': 'SMS',
    'summary': "Customizations for NP Collaborator Twilio SMS module",
    'description': """
Customizations for NP Collaborator Twilio SMS module
    """,
    'author': "Mark Dela Cruz",
    'website': 'https://www.markdelacruz.com',
    'depends': [
        'base',
        'twilio_sms_odoo',
        'npc_crm',
    ],
    'data': [
        'views/twilio_sms_views.xml',
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
