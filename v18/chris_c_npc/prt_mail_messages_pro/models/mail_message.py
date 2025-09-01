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

from odoo import api, fields, models
from odoo.exceptions import AccessError

from odoo.addons.mail.tools.discuss import Store


################
# Mail.Message #
################
class MailMessage(models.Model):
    _inherit = "mail.message"

    message_send_mode = fields.Selection(
        selection=[("odoo", "Odoo"), ("email", "Email")],
        default="odoo",
        help="Which mode was used to send a message",
    )

    partner_cc_ids = fields.Many2many(
        comodel_name="res.partner",
        string="CC",
        relation="mail_message_partner_cc_rel",
        column1="mail_message_id",
        column2="res_partner_id",
    )
    partner_bcc_ids = fields.Many2many(
        comodel_name="res.partner",
        string="BCC",
        relation="mail_message_partner_bcc_rel",
        column1="mail_message_id",
        column2="res_partner_id",
    )

    original_to_email = fields.Char()
    original_cc_email = fields.Char()

    # -- Check installed crm module
    @api.model
    def crm_not_installed(self):
        """Check installed crm module"""
        return (
            self.env["ir.module.module"].sudo().search([("name", "=", "crm")]).state
            != "installed"
        )

    @api.model_create_multi
    def create(self, vals_list):
        if not self._context.get("wizard_type_email"):
            return super().create(vals_list)
        cc_ids = self._context.get("cc_ids", [])
        bcc_ids = self._context.get("bcc_ids", [])
        for vals in vals_list:
            vals.update(message_send_mode="email")
            if cc_ids:
                vals.update(partner_cc_ids=[(4, partner_id) for partner_id in cc_ids])
            if bcc_ids:
                vals.update(partner_bcc_ids=[(4, partner_id) for partner_id in bcc_ids])
        return super().create(vals_list)

    # -- Undelete
    def undelete(self):
        """Undelete crm.lead message"""
        if self.crm_not_installed():
            return super().undelete()

        lead_ids = self.filtered(lambda rec: rec.model == "crm.lead").mapped("res_id")
        if lead_ids:
            self.env["crm.lead"].browse(lead_ids).write({"active": True})

        return super().undelete()

    # -- Archive crm lead messages
    @api.model
    def archive_lead_message(self, lead):
        """
        Set archive state for related mail messages
        :param lead: crm.lead record
        """
        msg = self.env["mail.message"].search(
            [
                ("active", "=", not lead.active),
                ("model", "=", "crm.lead"),
                ("res_id", "=", lead.id),
                ("message_type", "!=", "notification"),
            ]
        )
        values = {"active": lead.active}
        if lead.active:
            values.update(delete_uid=False, delete_date=False)
        msg.write(values)

    # -- Delete empty Leads
    def _delete_leads(self, leads_ids):
        """
        Deletes all leads with no messages left.
        Notifications are not considered!
        :param leads_ids: List of lead ids
        :return: empty.
        """
        if self.crm_not_installed():
            return

        if not leads_ids:
            return

        # Delete empty Leads
        lead_archive = []
        lead_delete = []
        model = "crm.lead"

        for lead in leads_ids:
            message_all = self.with_context(active_test=False).search(
                [
                    ("res_id", "=", lead),
                    ("model", "=", model),
                    ("message_type", "!=", "notification"),
                ]
            )
            message_archive = message_all.filtered(lambda msg: msg.active)

            if not message_all:
                lead_delete.append(lead)
            elif not message_archive:
                lead_archive.append(lead)

        if lead_delete:
            self.env[model].browse(lead_delete).unlink()
        if lead_archive:
            crm_leads_ids = self.env[model].browse(lead_archive)
            crm_leads_ids.write({"active": False})
            for lead_id in crm_leads_ids:
                self.archive_lead_message(lead_id)

    # -- Unlink
    def unlink_pro(self):
        # Check access rights
        self.unlink_rights_check()

        partners = self.ref_partner_ids
        if self.env.user.partner_id not in partners:
            partners |= self.env.user.partner_id

        partners._bus_send(
            "mail.message/delete",
            {"message_ids": self.ids},
        )

        # Store lead ids from messages in case we want to delete empty leads later
        lead_ids = [rec.res_id for rec in self.sudo() if rec.model == "crm.lead"]

        # Unlink
        if self.env.user.has_group("prt_mail_messages_pro.group_lost"):
            # Check is deleting lost messages
            all_lost = True
            for rec in self.sudo():
                if rec.model and rec.res_id:
                    all_lost = False
                    break

            # All messages are "lost". Unlink them with sudo
            if all_lost:
                super(MailMessage, self.sudo()).unlink()
            else:
                super().unlink_pro()
        else:
            super().unlink_pro()

        # All done if CRM Lead is not presented in models (eg CRM not installed)
        if self.crm_not_installed():
            return

        # Delete empty leads and opportunities
        leads = (
            self.env["crm.lead"]
            .browse(lead_ids)
            .filtered(
                lambda lead: (lead.company_id.lead_delete and lead.type == "lead")
                or (lead.company_id.opp_delete and lead.type == "opportunity")
            )
        )

        if leads:
            self._delete_leads(leads.ids)

    def _to_store(self, store: Store, **kwargs):
        res = super()._to_store(store, **kwargs)
        for message in self.sudo():
            store.add(
                message,
                {
                    "originalToEmail": message.original_to_email,
                    "originalCcEmail": message.original_cc_email,
                    "messageSendMode": message.message_send_mode,
                    "cx_edit_message": message.cx_edit_message,
                    "partnerCc": [
                        {"id": p.id, "name": p.name} for p in message.partner_cc_ids
                    ],
                    "partnerBcc": [
                        {"id": p.id, "name": p.name} for p in message.partner_bcc_ids
                    ],
                },
            )
        return res

    # -- Move messages
    # flake8: noqa: C901
    def message_move(
        self, dest_model, dest_res_id, notify="0", lead_delete=False, opp_delete=False
    ):
        """
        Moves messages to a new record
        :return:
        :param Char dest_model: name of the new record model
        :param Integer dest_res_id: id of the new record
        :param Char notify: add notification to destination thread
            '0': 'Do not notify'
            '1': 'Log internal note'
            '2': 'Send message'
        :param Boolean lead_delete: delete CRM Leads with no messages left
        :param Boolean opp_delete: delete CRM Opportunities with no messages left
        :return: nothing, just return)
        """

        # -- Can move messages?
        if not self.env.user.has_group("prt_mail_messages.group_move"):
            raise AccessError(self.env._("You cannot move messages!"))

        # Prepare data for notifications. Store old record data
        old_records = []
        for message in self:
            old_records.append(
                {
                    "id": message.id,
                    "data": Store(message, for_current_user=True).get_result(),
                    "originalThread": {
                        "thread_id": message.res_id,
                        "thread_model": message.model,
                    },
                    "movedThread": {
                        "thread_id": dest_res_id,
                        "thread_model": dest_model,
                    },
                }
            )

        mail_message_obj = self.env["mail.message"]
        # Store leads from messages in case we want to delete empty leads later
        leads = False
        if lead_delete:
            lead_messages = mail_message_obj.search(
                [("id", "in", self.ids), ("model", "=", "crm.lead")]
            )

            # Check if Opportunities are deleted as well
            domain = [("id", "in", lead_messages.mapped("res_id"))]
            if not opp_delete:
                domain.append(("type", "=", "lead"))

            leads = self.env["crm.lead"].search(domain)

        # Get Conversations. Will check and delete empty ones later
        conversations = False
        conversation_messages = self.filtered(
            lambda m: m.model == "cetmix.conversation"
        )
        if conversation_messages:
            conversations = self.env["cetmix.conversation"].search(
                [("id", "in", conversation_messages.mapped("res_id"))]
            )

        # Get new parent message
        parent_message = mail_message_obj.search(
            [
                ("model", "=", dest_model),
                ("res_id", "=", dest_res_id),
                ("parent_id", "=", False),
            ],
            order="id asc",
            limit=1,
        )

        # Move messages
        if parent_message:
            self.sudo().write(
                {
                    "model": dest_model,
                    "res_id": dest_res_id,
                    "parent_id": parent_message.id,
                }
            )
        else:
            self.sudo().write(
                {"model": dest_model, "res_id": dest_res_id, "parent_id": False}
            )

        # Move attachments. Use sudo() to override access rules issues
        self.with_context(no_document=True).mapped("attachment_ids").sudo().write(
            {"res_model": dest_model, "res_id": dest_res_id}
        )

        # Notify followers of destination record
        if notify and notify != "0":
            subtype = "mail.mt_note" if notify == "1" else "mail.mt_comment"
            body = self.env._(
                "%(total)s messages moved to this record:", total=str(len(self))
            )
            # Add messages ref to body:
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            link_format = ' <a target="_blank" href="{}">{}</a>'
            for index, message in enumerate(self, start=1):
                body += link_format.format(
                    f"{base_url}/web#id={message.id}&model=mail.message&view_type=form",
                    self.env._("Message %s", str(index)),
                )
            self.env[dest_model].browse([dest_res_id]).message_post(
                body=body,
                subject=self.env._("Messages moved"),
                message_type="notification",
                subtype_xmlid=subtype,
                body_is_html=True,
            )
        # Delete empty Conversations
        if conversations:
            mail_message_obj._delete_conversations(conversations.ids)

        # Update notifications
        partners = self.ref_partner_ids
        if self.env.user.partner_id not in partners:
            partners |= self.env.user.partner_id

        partners._bus_send(
            "mail.message/move",
            {"message_ids": old_records},
        )

        # Update Conversation last message data if moved to Conversation
        if dest_model == "cetmix.conversation":
            conversation = self.env["cetmix.conversation"].browse(dest_res_id)
            if conversation.message_ids:  # To ensure
                messages = conversation.message_ids.sorted(
                    key=lambda m: m.id, reverse=True
                )
                conversation.update(
                    {
                        "last_message_post": messages[0].date,
                        "last_message_by": messages[0].author_id.id,
                    }
                )

        # Delete empty leads
        if not leads:
            return

        # Compose list of leads to unlink
        leads_2_delete = self.env["crm.lead"]
        for lead in leads:
            message_count = mail_message_obj.search_count(
                [
                    ("res_id", "=", lead.id),
                    ("model", "=", "crm.lead"),
                    ("message_type", "!=", "notification"),
                ]
            )
            if message_count == 0:
                leads_2_delete += lead

        # Delete leads with no messages
        if leads_2_delete:
            leads_2_delete.unlink()
