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

from odoo.tests import Form

from odoo.addons.mail.tests.common import MailCommon
from odoo.addons.prt_mail_messages.tests.common import MailMessageCommon


def module_crm_installed(method):
    def wrapper(self):
        if not self.is_module_crm_installed:
            return method(self)
        return

    return wrapper


class MailMessageProCommon(MailMessageCommon, MailCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.is_module_crm_installed = cls.env["mail.message"].crm_not_installed()

        cls.partner_to = cls.env["res.partner"].create(
            {"name": "Partner To", "email": "partnerTo@example.com"}
        )
        cls.partner_cc = cls.env["res.partner"].create(
            {"name": "Partner Cc", "email": "partnerCc@example.com"}
        )
        cls.partner_bcc = cls.env["res.partner"].create(
            {"name": "Partner Bcc", "email": "partnerBcc@exmaple.com"}
        )

        cls.test_record = cls.env["res.partner"].create(
            {"name": "Partner Record", "email": "partner@example.com"}
        )
        cls.test_record.message_subscribe(partner_ids=cls.res_partner_bob.ids)

        MailMessage = cls.env["mail.message"].with_user(cls.env.user)

        cls.message_for_quote = MailMessage.create(
            {
                "res_id": cls.test_record.id,
                "author_id": cls.partner_to.id,
                "model": "res.partner",
                "partner_ids": [(6, 0, cls.partner_to.ids)],
                "partner_cc_ids": [(6, 0, cls.partner_cc.ids)],
                "partner_bcc_ids": [(6, 0, cls.partner_bcc.ids)],
                "reply_to": "test.reply@example.com",
                "email_from": "test.from@example.com",
                "body": "Message Quote",
            }
        )

        if cls.is_module_crm_installed:
            return
        cls.lead_object = cls.env["crm.lead"].create(
            {
                "active": True,
                "name": "Test Lead",
                "partner_id": cls.test_record.id,
                "company_id": cls.env.ref("base.main_company").id,
                "type": "lead",
            }
        )

        cls.lead_message_1 = MailMessage.create(
            {
                "res_id": cls.lead_object.id,
                "model": "crm.lead",
                "reply_to": "test.reply@example.com",
                "email_from": "test.from@example.com",
                "body": "test1",
            }
        )
        cls.lead_message_2 = MailMessage.create(
            {
                "res_id": cls.lead_object.id,
                "model": "crm.lead",
                "reply_to": "test.reply@example.com",
                "email_from": "test.from@example.com",
                "body": "test2",
            }
        )

    def _create_compose_message(self, subject):
        form = Form(
            self.env["mail.compose.message"].with_context(
                default_composition_mode="comment",
                default_model="res.partner",
                default_res_ids=self.test_record.ids,
            )
        )
        form.wizard_type = "odoo"
        form.partner_ids.add(self.res_partner_kate)
        form.partner_ids.add(self.res_partner_mark)
        form.subject = subject
        form.body = "Test Odoo Mode"
        return form.save()
