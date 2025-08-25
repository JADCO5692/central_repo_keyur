# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
    'name': "NP Collaborator Calendar Customization",
    'version': '18.0.1.5',
    'category': '',
    'summary': "Customizations for NP Collaborator Calendar",
    'description': """
Customizations for NP Collaborator Calendar
    """,
    'author': "Mark Dela Cruz",
    'website': 'https://www.markdelacruz.com',
    'depends': [
        'base',
        'calendar',
        'appointment',
        'appointment_sms',
    ],
    'data': [
        'data/calendar_template_data.xml',
        'data/calendar_alarm_data.xml',
        'views/calendar_menu.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'assets': {
        'web.assets_backend': [
        ],
    },
    'license': 'LGPL-3',
}
