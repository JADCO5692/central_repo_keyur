# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
	'name': "NP Collaborator Subscription Customizations",
	'version': '18.0.1.2',
	'category': 'Sales/Subscriptions',
	'summary': "Customizations for Subscriptions module",
	'description': """
This module currently does the ff:\n
1) Fix the subscription mandate to always default to the current date 
if the start date is more 24 hrs
2) Remove Automate Payment Button on subscription page
    """,
	'author': "Mark Dela Cruz",
	'website': 'https://www.markdelacruz.com',
	'depends': [
		'base',
		'sale_subscription',
	],
	'data': [
		# 'data/ir_config_parameter_data.xml',
		'views/sale_views.xml',
		'views/sale_subscription_portal_templates.xml',
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
