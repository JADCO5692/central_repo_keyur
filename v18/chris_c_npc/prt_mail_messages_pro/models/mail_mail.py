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

from odoo import fields, models, tools


class MailMail(models.Model):
    _inherit = "mail.mail"

    email_bcc = fields.Char(string="Bcc", help="Blind carbon copy message recipients")

    def _prepare_outgoing_list(
        self, mail_server=False, recipients_follower_status=None
    ):
        result_list = super()._prepare_outgoing_list(
            mail_server=mail_server,
            recipients_follower_status=recipients_follower_status,
        )
        email_bcc_normalized = tools.email_normalize_all(self.email_bcc)
        if email_bcc_normalized:
            for res in result_list:
                res["email_to_normalized"] += email_bcc_normalized
        return result_list
