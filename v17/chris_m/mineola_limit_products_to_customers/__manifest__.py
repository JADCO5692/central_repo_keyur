# -*- coding: utf-8 -*-
{
    "name": "Mineola: Assign Product to Customers",
    "summary": (
        """
        This module allows the user to assign product to
        certain portal users. Portal users can only see products
        in those categories and their subcategories.
        """
    ),
    "author": "theERPbot",
    "website": "https://www.theerpbot.com",
    "version": "17.0.1.1.1",
    "development_status": "Production/Stable",
    "license": "OPL-1",
    "installable": True,
    "data": [
        'security/ir.model.access.csv'
        ,'views/custom_prod_list_views.xml'
        ,'views/res_partner_views.xml'
        ,'security/website_menu.xml'
    ],
    "images": [],
    "depends": ["website_sale"
                ,"mail"],
}