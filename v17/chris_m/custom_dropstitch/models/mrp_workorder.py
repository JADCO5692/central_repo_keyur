# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class CustomMrpWorkOrder(models.Model):
    _inherit = "mrp.workorder"

    custom_color_2 = fields.Many2one(
        comodel_name="product.product",
        string="Color 2",
        related="production_id.custom_color_2",
    )
    custom_color_3 = fields.Many2one(
        comodel_name="product.product",
        string="Color 3",
        related="production_id.custom_color_3",
    )
    custom_color_4 = fields.Many2one(
        comodel_name="product.product",
        string="Color 4",
        related="production_id.custom_color_4",
    )
    custom_color_5 = fields.Many2one(
        comodel_name="product.product",
        string="Color 5",
        related="production_id.custom_color_5",
    )
    custom_color_6 = fields.Many2one(
        comodel_name="product.product",
        string="Color 6",
        related="production_id.custom_color_6",
    )
    custom_color_7 = fields.Many2one(
        comodel_name="product.product",
        string="Color 7",
        related="production_id.custom_color_7",
    )

    def write(self, vals):
        if "workcenter_id" in vals:
            workcenter_rec = self.env["mrp.workcenter"].browse(vals["workcenter_id"])
            if workcenter_rec:
                if self.production_id and workcenter_rec.custom_machine_no:
                    self.production_id.custom_machine_no = (
                        workcenter_rec.custom_machine_no
                    )
        return super(CustomMrpWorkOrder, self).write(vals)

    def button_start(self):
        for wo in self:
            if wo.state not in ["ready", "progress"]:
                raise UserError(
                    _(
                        "Cannot Start. All raw materials/components for this operation are not available"
                    )
                )

        res = super().button_start()
        return res
