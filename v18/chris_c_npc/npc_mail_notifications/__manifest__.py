# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
    'name': "NP Collaborator Email Notification Customizations",
    'version': '18.0.0.1',
    'category': 'Mail',
    'summary': "Customizations for NP Collaborator email notification",
    'description': """
Customizations for NP Collaborator email notification
    """,
    'author': "Mark Dela Cruz",
    'website': 'https://www.markdelacruz.com',
    'depends': [
        'mail',
    ],
    'data': [
        'views/mail_notif_views.xml',
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
