# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

import logging

_logger = logging.getLogger(__name__)


class ShipstationErrorInfo(models.TransientModel):
    _name = "shipstation.error.info"
    _description = "Shipstation Order Error Information Wizard"


    order_number = fields.Char(string="Order Number")
    action = fields.Char(string="Action")
    reason = fields.Text(string="Reason of Error")
    success_record_id = fields.Many2one(comodel_name='shipstation.error.show')
    failed_record_id = fields.Many2one(comodel_name='shipstation.error.show')



class ShipstationErrorShow(models.TransientModel):
    _name = "shipstation.error.show"
    _description = "Shipstation Order Error Show Wizard"
    total_success = fields.Integer(string="Total Success")
    total_failed = fields.Integer(string="Total Failed")
    success_records = fields.One2many(comodel_name='shipstation.error.info', inverse_name="success_record_id", string="Success Records")
    failed_records = fields.One2many(comodel_name='shipstation.error.info', inverse_name="failed_record_id", string="Failed Records")
