# -*- coding: utf-8 -*-
{
    "name": "Pmall Integration",
    "summary": (
        """
        Pmall Integration
        """
    ), 
    "version": "17.0.0.0.6",
    "license": "LGPL-3",
    "installable": True,
    "application": True,
    "data": [
        "security/ir.model.access.csv",
        "data/cron.xml",
        "data/data.xml",
        "views/pmall_config_view.xml",
        "views/pmall_order_logs_view.xml",
        "views/order_create_error_log.xml",
        "views/res_partner_view.xml", 
        "views/pmall_product_mapping.xml", 
        "views/sale_order.xml", 
    ],
    "assets": {},
    "images": [],
    "depends": [
        "sale",
        "website_sale",
        "custom_dropstitch"
    ],
}
