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

from odoo import models
from odoo.tools.mail import email_split_and_format


class IrMailServer(models.Model):
    _inherit = "ir.mail_server"

    def build_email(self, *args, **kwargs):
        # Get email message
        message_id = kwargs.get("message_id")
        if message_id:
            mail = self.env["mail.mail"].search(
                [("message_id", "=", message_id)], limit=1
            )
            if mail and mail.email_cc:
                # Email Cc update
                kwargs.update(email_cc=email_split_and_format(mail.email_cc))
            if mail and mail.email_bcc:
                # Email Bcc update
                kwargs.update(email_bcc=email_split_and_format(mail.email_bcc))
        return super().build_email(*args, **kwargs)
