# -*- coding: utf-8 -*-
{
    'name': 'custom',
    "version": "18.0.0.0.9",
    'category': 'Sales',
    'summary': 'Custom Changes',
    'description': """
     Custom changes.
    """,
    'depends': ['website_sale', 'web', 'point_of_sale', 'sale', 'pos_online_payment'],
    'data': [
        'data/mail_template.xml',
        'views/website_custom_checkout.xml',
        'views/res_partner.xml',
        'views/custom_template.xml',
        'views/website_sale.xml',
        'views/stock_picking.xml',
        'views/stock_picking_list.xml',
        'views/custom_pin_template_account.xml',
        'views/thankyou_template_page.xml',
        'views/sale_order.xml',
        'views/company.xml',
        'views/delivery_carrier.xml',
    ],
    "development_status": "Production/Stable",
    "license": "LGPL-3",
    'installable': True,
    'assets': {
        'point_of_sale._assets_pos': [
            'custom/static/src/xml/views/online_payment_popup_inherit.xml',
            'custom/static/src/js/online_payment_popup_patch.js',
            'custom/static/src/js/payment_screen_patch.js',
        ],
        'web.assets_frontend': [
            'custom/static/src/js/custom_shop_website.js',
            'custom/static/src/js/custom_checkout.js',
            'custom/static/src/js/custom_delivery_checkout.js',
            'custom/static/src/xml/views/add_to_cart_modified.xml',
            'custom/static/src/js/custom_cart_notification.js',
            'custom/static/src/css/loader.css',
        ],
    }
}
