# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
    'name': "Handle Notifications by Both Email and Inbox",
    'version': '18.0.1.0',
    'category': "Discuss",
    'summary': "Handle Notifications by Both Email and Discuss Inbox",
    'description': """
Odoo by default provides options for user to handle their notifications by either email or inbox.
This module gives an option for both.
    """,
    'author': "Mark Dela Cruz",
    'website': 'https://www.markdelacruz.com',
    'depends': [
        'base',
        'mail',
    ],
    'data': [
        'views/res_users_views.xml',
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
