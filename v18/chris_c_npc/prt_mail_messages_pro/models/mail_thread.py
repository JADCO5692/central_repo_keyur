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

import logging
import threading

from odoo import SUPERUSER_ID, api, fields, models
from odoo.modules.registry import Registry
from odoo.tools import formataddr
from odoo.tools.misc import clean_context

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    @api.model
    def message_parse(self, message, save_original=False):
        msg_dict = super().message_parse(message, save_original=save_original)
        msg_dict.update(
            original_to_email=", ".join(msg_dict.get("to", "").split(",")),
            original_cc_email=", ".join(msg_dict.get("cc", "").split(",")),
        )
        return msg_dict

    def _get_message_create_valid_field_names(self):
        field_names = super()._get_message_create_valid_field_names()
        return field_names | {"original_to_email", "original_cc_email"}

    def _check_can_update_message_content(self, messages):
        """Override method"""
        # Custom check update message content
        for message in messages:
            if not message.with_user(self.env.user.id)._message_can_edit():
                raise models.UserError(
                    self.env._("Not enough access rights to edit/delete this message")
                )
        return super()._check_can_update_message_content(messages)

    def _message_update_content_after_hook(self, message):
        if self._name == "discuss.channel":
            return super()._message_update_content_after_hook(message)
        user_partner = self.env.user.partner_id
        message.write(
            {
                "cx_edit_uid": self.env.user.id,
                "cx_edit_date": fields.datetime.now(),
            }
        )
        for msg in message:
            partners = msg.ref_partner_ids
            if user_partner not in partners:
                partners |= user_partner

            partners._bus_send(
                "message_updated",
                {
                    "action": "edit",
                    "message_ids": [
                        {
                            "id": msg.id,
                            "body": msg.body,
                            "cx_edit_message": msg.cx_edit_message,
                        }
                    ],
                },
            )

        return super()._message_update_content_after_hook(message)

    @api.model
    def append_email_address_in_email(self, list_ids):
        return ", ".join(
            [
                formataddr((p.name or "False", p.email or "False"))
                for p in self.env["res.partner"].browse(list_ids)
            ]
        )

    def _notify_thread_by_email(
        self,
        message,
        recipients_data,
        msg_vals=False,
        mail_auto_delete=True,  # mail.mail
        model_description=False,
        force_email_company=False,
        force_email_lang=False,  # rendering
        resend_existing=False,
        force_send=True,
        send_after_commit=True,  # email send
        subtitles=None,
        **kwargs,
    ):
        if not self._context.get("to_ids"):
            return super()._notify_thread_by_email(
                message,
                recipients_data,
                msg_vals=msg_vals,
                mail_auto_delete=mail_auto_delete,  # mail.mail
                model_description=model_description,
                force_email_company=force_email_company,
                force_email_lang=force_email_lang,  # rendering
                resend_existing=resend_existing,
                force_send=force_send,
                send_after_commit=send_after_commit,  # email send
                subtitles=subtitles,
                **kwargs,
            )

        template_values = self._notify_by_email_prepare_rendering_context(
            message,
            msg_vals=msg_vals,
            model_description=model_description,
            force_email_company=force_email_company,
            force_email_lang=force_email_lang,
        )  # 10 queries
        if subtitles:
            template_values["subtitles"] = subtitles

        email_layout_xmlid = (
            msg_vals.get("email_layout_xmlid") or message.email_layout_xmlid
        )
        template_xmlid = email_layout_xmlid or "mail.mail_notification_layout"
        mail_values = self._notify_by_email_get_base_mail_values(
            message, additional_values={"auto_delete": mail_auto_delete}
        )

        render_values = {**template_values, "actions": []}
        mail_body = self.env["ir.qweb"]._render(
            template_xmlid,
            render_values,
            minimal_qcontext=True,
            raise_if_not_found=False,
            lang=template_values["lang"],
        )
        if not mail_body:
            _logger.warning(
                "QWeb template %s not found or is empty "
                "when sending notification emails. "
                "Sending without layouting.",
                template_xmlid,
            )
            mail_body = message.body
        mail_body = self.env["mail.render.mixin"]._replace_local_links(mail_body)

        mail_values.update(body_html=mail_body)
        for key_ctx, key_rec in [
            ("to_ids", "email_to"),
            ("cc_ids", "email_cc"),
            ("bcc_ids", "email_bcc"),
        ]:
            if value := self._context.get(key_ctx):
                mail_values[key_rec] = self.append_email_address_in_email(value)

        email = (
            self.env["mail.mail"]
            .sudo()
            .with_context(**clean_context(self._context))
            .create(mail_values)
        )

        force_send = self._context.get("mail_notify_force_send", force_send)
        test_mode = getattr(threading.current_thread(), "testing", False)
        if force_send and (not self.pool._init or test_mode):
            # unless asked specifically, send emails after the transaction to
            # avoid side effects due to emails being sent while the transaction fails
            if not test_mode and send_after_commit:
                email_ids = email.ids
                dbname = self.env.cr.dbname
                _context = self._context

                @self.env.cr.postcommit.add
                def send_notifications():
                    with Registry(dbname).cursor() as cr:
                        env = api.Environment(cr, SUPERUSER_ID, _context)
                        env["mail.mail"].browse(email_ids).send()

            else:
                email.send()

        return True
