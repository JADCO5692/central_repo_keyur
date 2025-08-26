# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

import logging

_logger = logging.getLogger(__name__)


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    custom_bom_item_image = fields.Binary(string="BoM Image")
    custom_var_image = fields.Binary(
        string="Item Image", related="product_id.image_1920"
    )

class MrpBom(models.Model):
    _inherit = "mrp.bom"

    custom_bom_id = fields.Many2one('custom.product.bom','BOM Created From')
