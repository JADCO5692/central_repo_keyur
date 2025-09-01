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

from email.utils import parseaddr

from odoo.exceptions import MissingError
from odoo.tests import Form, tagged

from .common import MailMessageProCommon


@tagged("post_install", "-at_install")
class TestMessagePartnerAssign(MailMessageProCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.mail_message_test_1.write(
            {
                "author_id": False,
                "email_from": cls.res_partner_kate.email,
            }
        )
        cls.mail_message_test_2 = cls.env["mail.message"].create(
            {
                "author_id": False,
                "author_allowed_id": cls.res_partner_kate.id,
                "body": "Test Body Child",
                "partner_ids": [],
                "parent_id": cls.mail_message_parent.id,
                "res_id": cls.res_partner_kate.id,
                "model": cls.res_partner_kate._name,
                "email_from": cls.res_partner_kate.email,
            }
        )
        name, email = parseaddr(cls.mail_message_test_1.email_from)
        cls.wizard = (
            cls.env["cx.message.partner.assign.wiz"]
            .with_context(default_name=name, default_email=email)
            .create({})
        )

    def test_is_same_domain(self):
        """This test covers the scenario when a same email changed"""
        expected_value = {
            "domain": {"partner_id": [("email", "=", self.res_partner_kate.email)]}
        }
        self.assertTrue(self.wizard.same_email)
        self.assertEqual(expected_value, self.wizard.is_same())
        self.wizard.same_email = False
        expected_value = {"domain": {"partner_id": []}}
        self.assertFalse(self.wizard.same_email)
        self.assertEqual(expected_value, self.wizard.is_same())

    def test_assign_one_invalid(self):
        """
        This test covers the scenario when assigns author
        to the current message and 'Assign To' partner field value not set.
        """
        with self.assertRaises(MissingError):
            self.wizard.assign_one()

    def test_assign_one_without_active_record(self):
        """
        This test covers the scenario when assigns author
        to the current message without active record.
        """
        with Form(self.wizard) as form:
            form.partner_id = self.res_partner_kate
        self.wizard.assign_one()
        self.assertFalse(self.mail_message_test_1.author_id)

    def test_assign_one_valid(self):
        """
        This test covers the valid scenario when assigns author
        to the current message.
        """
        with Form(self.wizard) as form:
            form.partner_id = self.res_partner_kate
        self.wizard.with_context(active_id=self.mail_message_test_1.id).assign_one()
        self.assertEqual(self.mail_message_test_1.author_id, self.res_partner_kate)

    def test_assign_all_invalid(self):
        """
        This test covers the invalid scenario when assign all
        unassigned messages with the same email in 'From'
        to the author and 'Assign To' field value not set.
        """
        with self.assertRaises(MissingError):
            self.wizard.assign_all()

    def test_assign_all_valid(self):
        """
        This test covers the valid scenario when assign all
        unassigned messages with the same email in 'From'
        to the author.
        """
        with Form(self.wizard) as form:
            form.partner_id = self.res_partner_kate
        self.wizard.assign_all()
        self.assertEqual(self.mail_message_test_1.author_id, self.res_partner_kate)
        self.assertEqual(self.mail_message_test_2.author_id, self.res_partner_kate)
