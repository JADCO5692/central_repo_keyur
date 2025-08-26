# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
{
    "name": "Website Partial Payment (Enterprise)",
    "version": "17.0.1.0.0",
    "author": "Acespritech Solutions Pvt. Ltd.",
    "summary": "This module allows Customer to do the Partial Payment from website",
    "description": """
        This module allows Customer to do the Partial Payment from website.
    """,
    "category": "website",
    "price": 40,
    "currency": "EUR",
    "depends": [
        "base",
        "website_sale",
        "sale",
        "account_payment",
        "account",
        "stock",
        "payment",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/payment_view.xml",
        "views/sale_portal_template.xml",
        "views/confirmation_template.xml",
        "views/sale_view.xml",
        "views/account_invoice_view.xml",
        "views/portal_partial_invoice_pay.xml",
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "aspl_website_partial_payment_ee/static/**/*",
        ],
    },
    "images": ["static/description/main_screenshot.jpg"],
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:   
