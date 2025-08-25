# -*- coding: utf-8 -*-
##########################################################################
# Author : Webkul Software Pvt. Ltd. (<https://webkul.com/>;)
# Copyright(c): 2017-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>;
##########################################################################
{
    "name": "Odoo Zoom meeting Integration",
    "summary": "Zoom, Zoom Meeting, Zoom Integration, Odoo Zoom Meeting Integration, Zoom Calendar, Odoo Zoom, Meeting, Zoom Meet, Meeting Via Zoom, Odoo Meeting Via Zoom,Zoom Meeting in Odoo,Odoo",
    "category": "Discuss",
    "description": "Odoo Zoom Meeting Integration module facilitates you to create the Zoom Meetings directly from Your Odoo Calendar. You can manage all the zoom meeting details in Odoo like meeting time, organizers, agenda, etc.",
    "author": "Webkul Software Pvt. Ltd.",
    "version": "1.0.1",
    'price': 99,
    'currency': 'USD',
    "website": "https://store.webkul.com/",
    "live_test_url": "http://odoodemo.webkul.com/?module=zoom_meeting",
    "depends": ["base", "calendar", "wk_wizard_messages", 'website'],
    "data": ['security/ir.model.access.csv',
             'views/templates.xml',
             'views/res_users_views.xml',
             'views/res_company_views.xml',
             'views/calendar_views.xml',
             'data/mail_template_data.xml',
             'wizard/meeting_wizard_views.xml'
             ],

    "images": ['static/description/Banner.gif'],
    "application": True,
    "installable": True,
    "auto_install": False,
    "license": "Other proprietary",
    "pre_init_hook": "pre_init_check",
}
