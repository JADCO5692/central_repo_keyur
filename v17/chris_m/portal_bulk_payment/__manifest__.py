{
    'name': 'Portal Payments In Bulk | Bulk Order Payment',
    'version': '17.0.1.0.4',
    "development_status": "Production/Stable",
    "license": "LGPL-3",
    'summary': 'User can make multiple orders payment in single payment by selecting all and pay in single transaction.',
    'sequence': 6,
    "author": "theERPbot",
    "website": "https://www.theerpbot.com",
    'category': 'website', 
    'description':"""
        User can make multiple orders payment in single payment by selecting all and pay in single transaction.'
    """, 
    'depends':['portal','sale'],
    'data':[
        'views/sale_portal_templates.xml',
        'views/account_portal_templates.xml',
        'views/payment_success.xml', 
    ],
    'assets': {
        'web.assets_frontend': [
            'portal_bulk_payment/static/src/js/portal/portal.js',
            'portal_bulk_payment/static/src/js/portal/PortalPrepayment.js',
            'portal_bulk_payment/static/src/js/signature_form/**/*',
            'portal_bulk_payment/static/src/scss/portal.scss',
            'portal_bulk_payment/static/src/xml/sign_dialog_btn.xml',
            'portal_bulk_payment/static/src/js/menu.js', 
         ],
         'web.assets_backend': []
    }, 
    'application': True,
    'installable': True,
    'auto_install': False,
}
