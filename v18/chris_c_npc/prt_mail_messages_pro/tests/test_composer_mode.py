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

from odoo.exceptions import UserError
from odoo.tests import Form, tagged
from odoo.tools import email_split
from odoo.tools.misc import mute_logger

from .common import MailMessageProCommon


@tagged("post_install", "-at_install")
class TestMailComposer(MailMessageProCommon):
    """
    Test mail composer 'Odoo' and 'Email' modes
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user_kate = cls.env["res.users"].create(
            {"name": "kate", "login": "kate_demo", "notification_type": "email"}
        )
        user_kate.partner_id.write({"name": "Kate", "email": "kate@example.com"})
        cls.res_partner_kate = user_kate.partner_id

    @mute_logger("odoo.addons.mail.models.mail_mail")
    def test_quote_email_mode(self):
        context = self.message_for_quote.reply_prep_context()
        form = Form(self.env["mail.compose.message"].with_context(**context))
        form.wizard_type = "email"
        compose = form.save()

        self.assertEqual(
            compose.partner_ids,
            self.partner_to,
            msg=f"Partner To must be equal to partner ID# {self.partner_to.id}",
        )
        self.assertFalse(compose.partner_cc_ids, msg="Partner Cc must be empty")
        self.assertFalse(compose.partner_bcc_ids, msg="Partner Bcc must be empty")

        context.update(wizard_mode="quote")
        form = Form(self.env["mail.compose.message"].with_context(**context))
        form.wizard_type = "email"
        compose = form.save()

        self.assertEqual(
            compose.partner_ids,
            self.partner_to,
            msg=f"Partner To must be equal to partner ID# {self.partner_to.id}",
        )
        self.assertEqual(
            compose.partner_cc_ids,
            self.partner_cc,
            msg=f"Partner Cc must be equal to partner ID# {self.partner_cc.id}",
        )
        self.assertEqual(
            compose.partner_bcc_ids,
            self.partner_bcc,
            msg=f"Partner Bcc must be equal to partner ID# {self.partner_bcc.id}",
        )

    @mute_logger("odoo.addons.mail.models.mail_mail")
    def test_odoo_mode(self):
        """Send a new message in Odoo mode"""

        # Send new message
        # recipients: Kate and Mike
        composer = self._create_compose_message("--Mail-Odoo-Mode--")
        with self.mock_mail_gateway():
            composer.action_send_mail()

        mails = self.env["mail.mail"].search([("subject", "=", "--Mail-Odoo-Mode--")])

        self.assertEqual(len(mails), 2, msg="Mail messages count must equal to 2")
        first_mail, second_mail = mails

        recipients = first_mail.recipient_ids
        self.assertEqual(len(recipients), 2)
        self.assertIn(self.res_partner_bob, recipients, msg="Bob must be recipient")
        self.assertIn(self.res_partner_mark, recipients, msg="Mike must be recipient")
        recipients = second_mail.recipient_ids
        self.assertEqual(len(recipients), 1)
        self.assertIn(self.res_partner_kate, recipients, msg="Kate must be recipient")

    @mute_logger("odoo.addons.mail.models.mail_mail")
    def test_email_mode(self):
        """Send a new message in Email mode"""

        # Send new message
        # record: partner Agrolait
        # recipients: Thomas Passot and Michel Fletcher
        # cc: Chao Wang
        # bcc: David Simpson
        composer = self._create_compose_message("--Mail-Email-Mode--")
        with Form(composer) as form:
            form.wizard_type = "email"
            form.partner_cc_ids.add(self.res_partner_ann)
            form.partner_bcc_ids.add(self.res_partner_target_record)
        with self.mock_mail_gateway():
            composer.action_send_mail()

        mail = self.env["mail.mail"].search([("subject", "=", "--Mail-Email-Mode--")])

        self.assertEqual(len(mail), 1)
        # Recipients field must be empty
        # Because all recipients are now in email_to field
        self.assertFalse(mail.recipient_ids, msg="Must be no recipients")

        # Extract email addresses
        # To:
        to_addrs = email_split(mail.email_to)
        self.assertEqual(len(to_addrs), 2, msg="Must be 2 addresses in the 'to:' field")

        self.assertIn(
            "kate@example.com",
            to_addrs,
            msg="'kate@example.com' must be in the 'to:' field",
        )
        self.assertIn(
            "mark@example.com",
            to_addrs,
            msg="'mark@example.com' must be in the 'to:' field",
        )

        # Cc:
        cc_addrs = email_split(mail.email_cc)
        self.assertEqual(len(cc_addrs), 1, msg="Must be 1 address in the 'cc:' field")
        self.assertIn(
            "ann@example.com",
            cc_addrs,
            msg="'ann@example.com' must be in the 'bcc:' field",
        )

        # Bcc:
        bcc_addrs = email_split(mail.email_bcc)
        self.assertEqual(len(bcc_addrs), 1, msg="Must be 1 address in the 'bcc:' field")
        self.assertIn(
            "target@example.com",
            bcc_addrs,
            msg="'target@example.com' must be in the 'cc:' field",
        )

    def test_compose_wizard_type(self):
        context = self.message_for_quote.reply_prep_context()
        context.update(default_subject="Test Compose")
        compose_obj = self.env["mail.compose.message"].with_context(**context)
        with self.assertRaises(UserError):
            compose_obj.create(
                {
                    "composition_mode": "mass_mail",
                    "wizard_type": "email",
                }
            )

        note_id = self.env["ir.model.data"]._xmlid_to_res_id("mail.mt_note")

        # Create a message in "Email" mode
        compose = compose_obj.create(
            {"composition_mode": "comment", "wizard_type": "email"}
        )
        # Check that "Email" mode is applied
        self.assertEqual(compose.wizard_type, "email")

        # Set subtype to "Note" and check that "Odoo" mode is applied
        compose_in_odoo_mode = compose_obj.with_context(
            **({"subtype_id": note_id, "wizard_type": "email"})
        ).create({})
        self.assertEqual(compose_in_odoo_mode.wizard_type, "odoo")

        # Remove subtype and check that "Odoo" mode is applied
        compose_in_odoo_mode = compose_obj.with_context(
            **({"subtype_id": False, "wizard_type": "email"})
        ).create({})
        self.assertEqual(compose_in_odoo_mode.wizard_type, "odoo")

        # Set subtype to "Note" and force create a message in "Email" mode
        # A UserError must be raised.
        with self.assertRaises(UserError):
            compose_obj.create({"subtype_id": note_id, "wizard_type": "email"})
