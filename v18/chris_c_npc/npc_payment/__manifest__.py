# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
	'name': "NP Collaborator Payment Customizations",
	'version': '18.0.1.0',
	'category': 'Accounting/Accounting',
	'summary': "Customizations for Payments",
	'description': """
This module currently does the ff:\n
1) Set invoice to 'Paid' payment state when the sum of all payment transactions
 that are in "Confirmed" state is equal to the amount due.
    """,
	'author': "Mark Dela Cruz",
	'website': 'https://www.markdelacruz.com',
	'depends': [
		'base',
		'account',
		'payment',
	],
	'data': [
		# 'data/ir_config_parameter_data.xml',
		# 'views/crm_views.xml',
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
