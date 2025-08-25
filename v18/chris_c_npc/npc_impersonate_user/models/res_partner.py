import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    can_be_impersonated = fields.Boolean(compute="_compute_can_be_impersonated")
    can_impersonate_user = fields.Boolean(compute="_compute_can_impersonate_user")

    def _compute_can_impersonate_user(self):
        for partner in self:
            partner.can_impersonate_user = self.env.user.has_group(
                "auth_impersonate_user.impersonate_admin_group"
            )

    def _compute_can_be_impersonated(self):
        for partner in self:
            if partner.user_ids:
                partner.can_be_impersonated = partner.user_ids[0].can_be_impersonated
            else:
                partner.can_be_impersonated = False

    def impersonate_user(self):
        self.ensure_one()
        if self.env.user.can_impersonate_user and self.user_ids:
            user = self.user_ids[0]
            user._update_last_login()
            return {
                "type": "ir.actions.act_url",
                "target": "self",
                "url": f"/web/impersonate?uid={user.id}",
            }
