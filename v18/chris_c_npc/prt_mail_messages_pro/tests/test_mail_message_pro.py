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

from odoo.tests import tagged

from .common import MailMessageProCommon, module_crm_installed


@tagged("post_install", "-at_install")
class TestMailMessagePro(MailMessageProCommon):
    @module_crm_installed
    def test_lead_undelete(self):
        messages = (
            self.env["mail.message"]
            .with_context(active_test=False)
            .search(
                [
                    ("res_id", "=", self.lead_object.id),
                    ("message_type", "!=", "notification"),
                ]
            )
        )
        messages.unlink_pro()

        self.assertFalse(self.lead_message_1.active)
        self.assertFalse(self.lead_message_2.active)
        self.assertFalse(self.lead_object.active)

        self.lead_message_1.undelete()

        self.assertTrue(self.lead_message_1.active)
        self.assertTrue(self.lead_object.active)

    @module_crm_installed
    def test_lead_unlink(self):
        messages = (
            self.env["mail.message"]
            .with_context(active_test=False)
            .search(
                [
                    ("res_id", "=", self.lead_object.id),
                    ("message_type", "!=", "notification"),
                ]
            )
        )
        messages.unlink_pro()
        messages.unlink_pro()

        Lead = self.env["crm.lead"]

        self.assertFalse(Lead.search([("id", "=", self.lead_message_1.id)]))
        self.assertFalse(Lead.search([("id", "=", self.lead_message_2.id)]))

    @module_crm_installed
    def test_lead_archive(self):
        messages = (
            self.env["mail.message"]
            .with_context(active_test=False)
            .search(
                [
                    ("res_id", "=", self.lead_object.id),
                    ("message_type", "!=", "notification"),
                ]
            )
        )
        messages.unlink_pro()

        self.assertFalse(self.lead_object.active)
        self.assertFalse(self.lead_message_1.active)
        self.assertFalse(self.lead_message_2.active)
