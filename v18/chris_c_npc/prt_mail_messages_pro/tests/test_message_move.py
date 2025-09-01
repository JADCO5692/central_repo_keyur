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

from odoo.exceptions import AccessError
from odoo.tests import Form, tagged

from .common import MailMessageProCommon


@tagged("post_install", "-at_install")
class TestMessageMove(MailMessageProCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_demo = cls.env.ref("base.user_demo")
        cls.conversation_test_1 = cls.env.ref(
            "prt_mail_messages.cetmix_conversation_test_1"
        )

    def test_user_doesnt_access_to_message_move(self):
        """
        This test covers the scenario when a user moving message without access group
        """
        form = Form(self.env["prt.message.move.wiz"].with_user(self.user_demo))
        wizard = form.save()
        with self.assertRaises(AccessError):
            wizard.message_move()

    def test_message_move_without_model_to(self):
        """This test covers the scenario when a 'Move To' record not set"""
        self.user_demo.write(
            {"groups_id": [(4, self.ref("prt_mail_messages.group_move"))]}
        )
        form = Form(self.env["prt.message.move.wiz"].with_user(self.user_demo))
        wizard = form.save()
        self.assertFalse(wizard.model_to)
        wizard.message_move()
        self.assertEqual(self.mail_message_test_1.res_id, self.res_partner_kate.id)
        self.assertEqual(self.mail_message_test_1.model, "res.partner")

    def test_message_move_without_context(self):
        """This test covers the scenario when a context not set"""
        self.user_demo.write(
            {"groups_id": [(4, self.ref("prt_mail_messages.group_move"))]}
        )
        form = Form(self.env["prt.message.move.wiz"].with_user(self.user_demo))
        form.model_to = f"res.partner,{self.res_partner_mark.id}"
        form.save().message_move()
        self.assertEqual(self.mail_message_test_1.res_id, self.res_partner_kate.id)
        self.assertEqual(self.mail_message_test_1.model, "res.partner")

    def test_message_move_with_thread_message(self):
        """This test covers the scenario when a user moving message"""
        self.user_demo.write(
            {"groups_id": [(4, self.ref("prt_mail_messages.group_move"))]}
        )
        form = Form(
            self.env["prt.message.move.wiz"]
            .with_user(self.user_demo)
            .with_context(thread_message_id=self.mail_message_test_1.id)
        )
        form.model_to = f"res.partner,{self.res_partner_mark.id}"
        form.save().message_move()
        self.assertEqual(self.mail_message_test_1.res_id, self.res_partner_mark.id)
        self.assertEqual(self.mail_message_test_1.model, "res.partner")

    def test_message_move_with_active_records(self):
        """This test covers the scenario when a user moving message"""
        self.user_demo.write(
            {"groups_id": [(4, self.ref("prt_mail_messages.group_move"))]}
        )
        form = Form(
            self.env["prt.message.move.wiz"]
            .with_user(self.user_demo)
            .with_context(active_ids=self.mail_message_test_1.ids)
        )
        form.model_to = f"res.partner,{self.res_partner_mark.id}"
        form.save().message_move()
        self.assertEqual(self.mail_message_test_1.res_id, self.res_partner_mark.id)
        self.assertEqual(self.mail_message_test_1.model, "res.partner")

    def test_message_move_for_conversation(self):
        """
        This test covers the scenario when a user
        moving message for conversation record
        """
        self.mail_message_test_1.write(
            {
                "model": "cetmix.conversation",
                "res_id": self.conversation_test_1.id,
            }
        )
        self.user_demo.write(
            {"groups_id": [(4, self.ref("prt_mail_messages.group_move"))]}
        )
        form = Form(
            self.env["prt.message.move.wiz"]
            .with_user(self.user_demo)
            .with_context(active_ids=self.conversation_test_1.ids)
        )
        form.model_to = f"res.partner,{self.res_partner_mark.id}"
        wizard = form.save()
        self.assertFalse(wizard.is_conversation)
        wizard = wizard.with_context(active_model="cetmix.conversation")
        self.assertTrue(wizard.is_conversation)
        wizard.sudo().message_move()
        self.assertEqual(self.mail_message_test_1.res_id, self.res_partner_mark.id)
        self.assertEqual(self.mail_message_test_1.model, "res.partner")
