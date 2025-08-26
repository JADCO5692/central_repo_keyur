from odoo import fields, models, api, _

import logging

_logger = logging.getLogger(__name__)
from odoo.osv import expression


class CustomPurchaseOrder(models.Model):
    _inherit = "purchase.order"

    custom_allowed_supplier_ids = fields.Many2many(
        "res.partner",
        compute="_compute_allowed_supplier_ids",
        string="Allowed Supplier",
    )

    @api.depends("partner_id")
    def _compute_allowed_supplier_ids(self):
        for order in self:
            if order.partner_id:
                order.custom_allowed_supplier_ids = (
                    order.partner_id.custom_allowed_supplier_ids
                )
            else:
                order.custom_allowed_supplier_ids = []

    def _get_product_catalog_domain(self):
        return expression.AND(
            [
                super()._get_product_catalog_domain(),
                [
                    "|",
                    ("seller_ids.partner_id", "=", self.partner_id.id),
                    (
                        "seller_ids.partner_id",
                        "in",
                        self.custom_allowed_supplier_ids.ids,
                    ),
                ],
            ]
        )

    @api.onchange("partner_id")
    def _onchange_custom_partner_id(self):
        for order in self:
            if order.partner_id.custom_receipt_type_id:
                order.picking_type_id = order.partner_id.custom_receipt_type_id
