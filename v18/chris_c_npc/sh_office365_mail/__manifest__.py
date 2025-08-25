# Part of Softhealer Technologies.
{
    'name' : 'Office 365 - Odoo Mail',

    "author": "Softhealer Technologies",

    "license": "OPL-1",

    "website": "https://www.softhealer.com",

    "support": "support@softhealer.com",

    "version": "0.0.1",

    "category": "Extra Tools",

    "summary": "Odoo Office 365 Connectors Office 365 with Odoo integration Odoo Office 365 Mail Sync Odoo Office 365 Mail API Office 365 Mail Integration Office 365 Email Integration Odoo Mail Connector Mail Connectors Office 365 Mail Connector MS Office 365 Mail Connector Microsoft Office 365 Mail Connector Office Mail Connector Microsoft Office Mail Connector MS Office Mail Connector Mail Integration Office 365 Mail Integration MS Office 365 Mail Integration Email Connector Email Connectors Office 365 Email Connector MS Office 365 Email Connector Microsoft Office 365 Email Connector Office Email Connector Microsoft Office Email Connector MS Office Email Connector Email Integration Office 365 Email Integration MS Office 365 Email Integration Microsoft Office 365 Mail Integration Office Mail Integration MS Office Mail Integration Microsoft Office Mail Integration Office 365 Mail Sync MS Office 365 Mail Sync Microsoft Office 365 Mail Sync  Office Mail Sync Microsoft Office Mail Sync  MS Office Mail Sync Mails Connector Microsoft Office 365 Email Integration Office Email Integration MS Office Email Integration Microsoft Office Email Integration Office 365 Email Sync MS Office 365 Email Sync Microsoft Office 365 Email Sync Office Email Sync Microsoft Office Email Sync MS Office Email Sync Emails Connector",

    "description": """Nowadays, Office 365 is a widely used cloud-based application. Here in odoo there are no options to sync your office-365 mails. Using this application you can sync your office-365 mails with odoo in just one click.""",
    'depends' : ['base_setup','sh_office365_base','contacts'],
    'data' : [
        'data/sh_office365_config_data.xml',
        'views/sh_office365_config_views.xml',
    ],
    'demo' : [],
    'installation': True,
    'application' : True,
    'auto_install' : False,
    "images": ["static/description/background.png", ],
    "price": "25",
    "currency": "EUR"
}
