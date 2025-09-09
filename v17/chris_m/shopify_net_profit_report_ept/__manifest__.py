# -*- coding: utf-8 -*-
{
    'name': "Shopify Net Profit Report Ept",

    'summary': """
        Visible Net Profit report for shopify all instances.""",

    'description': """
        Visible Net Profit report for shopify all instances.
    """,

    'author': "Emipro Technologies Pvt. Ltd.",
    'website': "http://www.emiprotechnologies.com",

    'license': 'OPL-1',
    'category': 'Account',
    'version': '0.1',

    'depends': ['account_accountant', 'shopify_ept'],

    'data': [
        'data/net_profit_report_data.xml',
        'report/net_profit_report.xml',
        
    ],
}
