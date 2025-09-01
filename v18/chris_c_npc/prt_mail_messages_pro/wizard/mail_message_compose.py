###################################################################################
#
#    Copyright (C) 2020 Cetmix OÜ
#
#   Odoo Proprietary License v1.0
#
#   This software and associated files (the "Software") may only be used (executed,
#   modified, executed after modifications) if you have purchased a valid license
#   from the authors, typically via Odoo Apps, or if you have received a written
#   agreement from the authors of the Software (see the COPYRIGHT file).
#
#   You may develop Odoo modules that use the Software as a library (typically
#   by depending on it, importing it and using its resources), but without copying
#   any source code or material from the Software. You may distribute those
#   modules under the license of your choice, provided that this license is
#   compatible with the terms of the Odoo Proprietary License (For example:
#   LGPL, MIT, or proprietary licenses similar to this one).
#
#   It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#   or modified copies of the Software.
#
#   The above copyright notice and this permission notice must be included in all
#   copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#   IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#   DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#   ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#   DEALINGS IN THE SOFTWARE.
#
###################################################################################

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class MailComposer(models.TransientModel):
    _inherit = "mail.compose.message"

    def _default_wizard_type(self):
        """Set wizard type"""
        return self.env.user.wizard_type

    wizard_type = fields.Selection(
        [("odoo", "Odoo"), ("email", "E-Mail")],
        string="Mail Composer Mode",
        default=lambda self: self._default_wizard_type(),
        required=True,
        help="Odoo: use regular Odoo messaging flow\n"
        "E-Mail: use classic email mode with CC and BCC fields\n"
        "Important:"
        " existing followers well be notified regular way according to settings",
    )

    partner_cc_ids = fields.Many2many(
        string="CC",
        comodel_name="res.partner",
        relation="mail_composer_partner_cc_rel",
        column1="message_id",
        column2="partner_id",
    )
    partner_bcc_ids = fields.Many2many(
        string="BCC",
        comodel_name="res.partner",
        relation="mail_composer_partner_bcc_rel",
        column1="message_id",
        column2="partner_id",
    )
    message_type = fields.Selection(
        selection_add=[("email_outgoing", "Outgoing Email")],
        ondelete={"email_outgoing": "set default"},
    )

    @api.constrains("wizard_type")
    def _check_wizard_type(self):
        for rec in self:
            if (
                rec.composition_mode != "comment" or rec.subtype_is_log
            ) and rec.wizard_type == "email":
                raise UserError(
                    _('"Email mode" cannot be used in such wizard configuration')
                )

    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)

        wizard_mode = self._context.get("wizard_mode") or result.get("wizard_mode")

        # Add CC/BCC from parent message if quote mode is used
        parent_id = result.get("parent_id")
        if wizard_mode == "quote" and parent_id:
            msg = self.env["mail.message"].browse(parent_id)
            result.update(
                partner_cc_ids=[Command.set(msg.partner_cc_ids.ids)],
                partner_bcc_ids=[Command.set(msg.partner_bcc_ids.ids)],
            )

        # Check if message is an internal note and force the "odoo" mode if yes
        subtype_note_id = self.env["ir.model.data"]._xmlid_to_res_id("mail.mt_note")
        subtype_id = result.get("subtype_id")
        # If composition mode is not "Comment or message subtype is not "Note"
        # or subtype is not set (default is "Note")
        if (
            result.get("composition_mode") != "comment"
            or subtype_id == subtype_note_id
            or not subtype_id
        ):
            result.update(wizard_type="odoo")
        return result

    def _action_send_mail(self, auto_commit=False):
        if self.wizard_type == "email" and not self.subtype_is_log:
            self.message_type = "email_outgoing"
            self = self.with_context(
                to_ids=self.partner_ids.ids,
                cc_ids=self.partner_cc_ids.ids,
                bcc_ids=self.partner_bcc_ids.ids,
                wizard_type_email=True,
            )
        return super()._action_send_mail(auto_commit=auto_commit)
