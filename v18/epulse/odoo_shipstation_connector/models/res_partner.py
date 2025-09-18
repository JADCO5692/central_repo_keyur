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

import base64
import json
import logging
import requests

from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ResPartnerData(models.Model):
    _inherit = 'res.partner'

    shipstation_customer_id = fields.Integer('Shipstation Customer ID', default=-1)
    is_shipstation_customer = fields.Boolean('Shipstation Customer')
    shipstation_user_id = fields.Many2one('shipstation.configuration', string="Shipstatino User")
