# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
	'name': "NP Collaborator Mail Helpdesk",
	'version': '18.0.1.2',
	'category': 'Helpdesk',
	'summary': "Create helpdesk tickets for all incoming customer messages",
	'description': """
This module currently does the ff:\n
1) Create a new ticket for all incoming customer messages
    """,
	'author': "Mark Dela Cruz",
	'website': 'https://www.markdelacruz.com',
	'depends': [
		'base',
		'mail',
		'helpdesk',
	],
	'data': [
		'data/helpdesk_team_data.xml',
		'views/helpdesk_views.xml',
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
