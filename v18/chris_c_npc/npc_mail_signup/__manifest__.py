# -*- coding: utf-8 -*-
# noinspection PyStatementEffect
{
	'name': "NP Signup Mail Link Expiry",
	'version': '18.0.0.0',
	'category': 'Hidden/Tools',
	'summary': "Add portal access link's validity on sign-up email.",
	'description': """
Add portal access link's validity on sign-up email.""",
	'author': "Mark Dela Cruz",
	'website': 'https://www.markdelacruz.com',
	'depends': [
		'auth_signup',
	],
	'data': [
		'views/mail_template.xml',
	],
	'demo': [
	],
	'installable': True,
	'application': False,
	'assets': {
		'web.assets_backend': [],
	},
	'license': 'LGPL-3',
}
