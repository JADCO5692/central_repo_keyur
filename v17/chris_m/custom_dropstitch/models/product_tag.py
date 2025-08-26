# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import logging

_logger = logging.getLogger(__name__)


class ProductTag(models.Model):
    _inherit = "product.tag"

    custom_color_1 = fields.Integer("Color Tag", default=1)
