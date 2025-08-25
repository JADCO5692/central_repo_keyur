from odoo import models, fields, api, Command
import logging

_logger = logging.getLogger(__name__)


class Users(models.Model):
    _inherit = 'res.users'

    notification_type = fields.Selection(
        selection_add=[('email_inbox', "Handle by Emails and in Odoo")],
        ondelete={'email_inbox': 'cascade'})

    @api.depends('share', 'groups_id')
    def _compute_notification_type(self):
        """ Override so that if user is added in inbox group,
        their notification_type must be set to either 'inbox' or 'email_inbox';
        for portal users, it should be always set to 'email'
        """
        inbox_group_id = self.env['ir.model.data']._xmlid_to_res_id('mail.group_mail_notification_type_inbox')

        self.filtered_domain([
            ('groups_id', 'in', inbox_group_id), ('notification_type', 'not in', ('inbox', 'email_inbox'))
        ]).notification_type = 'inbox'
        self.filtered_domain([
            ('groups_id', 'not in', inbox_group_id), ('notification_type', 'in', ('inbox', 'email_inbox'))
        ]).notification_type = 'email'

        # Special case: internal users with inbox notifications converted to portal must be converted to email users
        self.filtered_domain([
            ('share', '=', True),
            ('notification_type', 'in', ('inbox', 'email_inbox'))
        ]).notification_type = 'email'

    def _inverse_notification_type(self):
        """ Override so that if user selects inbox or email_inbox as notification_type
        they will be in inbox group
        """
        inbox_group = self.env.ref('mail.group_mail_notification_type_inbox')
        inbox_users = self.filtered(lambda user: user.notification_type in ('inbox', 'email_inbox'))
        inbox_users.write({'groups_id': [Command.link(inbox_group.id)]})
        (self - inbox_users).write({'groups_id': [Command.unlink(inbox_group.id)]})
