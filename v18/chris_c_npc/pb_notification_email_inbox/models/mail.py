from odoo import models, fields, api, Command
from odoo.tools import clean_context, split_every
import threading
import logging
from pprint import pprint

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _notify_thread(self, message, msg_vals=False, **kwargs):
        recipients_data = super()._notify_thread(message, msg_vals=msg_vals, **kwargs)

        scheduled_date = self._is_notification_scheduled(kwargs.pop('scheduled_date', None))
        if not scheduled_date:
            self._notify_thread_by_email_inbox(message, recipients_data, msg_vals=msg_vals, **kwargs)

        return recipients_data

    def _notify_thread_by_email_inbox(
            self,
            message,
            recipients_data,
            msg_vals=False,
            mail_auto_delete=True,  # mail.mail
            model_description=False,
            force_email_company=False,
            force_email_lang=False,
            # rendering
            subtitles=None,  # rendering
            resend_existing=False,
            force_send=True,
            send_after_commit=True,  # email send
            **kwargs):
        """ Notify recipient by email and on their inbox. It does three main things :

          * create inbox notifications for users;
          * send bus notifications;
          * send email

        :param record message: <mail.message> record being notified. May be
          void as 'msg_vals' superseeds it;
        :param list recipients_data: list of recipients data based on <res.partner>
          records formatted like [
          {
            'active': partner.active;
            'id': id of the res.partner being recipient to notify;
            'is_follower': follows the message related document;
            'lang': its lang;
            'groups': res.group IDs if linked to a user;
            'notif': 'inbox', 'email', 'sms' (SMS App);
            'share': is partner a customer (partner.partner_share);
            'type': partner usage ('customer', 'portal', 'user');
            'ushare': are users shared (if users, all users are shared);
          }, {...}]. See ``MailThread._notify_get_recipients()``;
        :param dict msg_vals: values dict used to create the message, allows to
          skip message usage and spare some queries;

        :param bool mail_auto_delete: delete notification emails once sent;

        :param str model_description: description of current model, given to
          avoid fetching it and easing translation support;
        :param record force_email_company: <res.company> record used when rendering
          notification layout. Otherwise, computed based on current record;
        :param str force_email_lang: lang used when rendering content, used
          notably to compute model name or translate access buttons;
        :param list subtitles: optional list set as template value "subtitles";

        :param bool resend_existing: check for existing notifications to update
          based on mailed recipient, otherwise create new notifications;
        :param bool force_send: send emails directly instead of using queue;
        :param bool send_after_commit: if force_send, tells to send emails after
          the transaction has been committed using a post-commit hook;
        """

        partners_data = [r for r in recipients_data if r['notif'] == 'email_inbox']
        if not partners_data:
            return True

        # SEND ON INBOX
        inbox_pids_uids = sorted(
            [(r['id'], r['uid']) for r in partners_data]
        )
        if inbox_pids_uids:
            notif_create_values = [
                {
                    "author_id": message.author_id.id,
                    "mail_message_id": message.id,
                    "notification_status": "sent",
                    "notification_type": "inbox",
                    "res_partner_id": pid_uid[0],
                }
                for pid_uid in inbox_pids_uids
            ]
            # sudo: mail.notification - creating notifications is the purpose of notify methods
            self.env["mail.notification"].sudo().create(notif_create_values)
            users = self.env['res.users'].browse(i[1] for i in inbox_pids_uids if i[1])
            # sudo: mail.followers - reading followers of target users in batch to send it to them
            followers = self.env["mail.followers"].sudo().search(
                [
                    ('res_model', '=', message.model),
                    ('res_id', '=', message.res_id),
                    ('partner_id', 'in', users.partner_id.ids),
                ]
            )
            for user in users:
                user._bus_send_store(
                    message.with_user(user).with_context(allowed_company_ids=[]),
                    msg_vals=msg_vals,
                    for_current_user=True,
                    add_followers=True,
                    followers=followers,
                    notification_type="mail.message/inbox",
                )

        # SEND BY EMAIL
        base_mail_values = self._notify_by_email_get_base_mail_values(
            message,
            additional_values={'auto_delete': mail_auto_delete}
        )

        # Clean the context to get rid of residual default_* keys that could cause issues during
        # the mail.mail creation.
        # Example: 'default_state' would refer to the default state of a previously created record
        # from another model that in turns triggers an assignation notification that ends up here.
        # This will lead to a traceback when trying to create a mail.mail with this state value that
        # doesn't exist.
        SafeMail = self.env['mail.mail'].sudo().with_context(clean_context(self._context))
        SafeNotification = self.env['mail.notification'].sudo().with_context(clean_context(self._context))
        emails = self.env['mail.mail'].sudo()

        # loop on groups (customer, portal, user,  ... + model specific like group_sale_salesman)
        gen_batch_size = int(
            self.env['ir.config_parameter'].sudo().get_param('mail.batch_size')
        ) or 50  # be sure to not have 0, as otherwise no iteration is done
        notif_create_values = []
        for _lang, render_values, recipients_group in self._notify_get_classified_recipients_iterator(
                message,
                partners_data,
                msg_vals=msg_vals,
                model_description=model_description,
                force_email_company=force_email_company,
                force_email_lang=force_email_lang,
                subtitles=subtitles,
        ):
            # generate notification email content
            mail_body = self._notify_by_email_render_layout(
                message,
                recipients_group,
                msg_vals=msg_vals,
                render_values=render_values,
            )
            recipients_ids = recipients_group.pop('recipients')

            # create email
            for recipients_ids_chunk in split_every(gen_batch_size, recipients_ids):
                mail_values = self._notify_by_email_get_final_mail_values(
                    recipients_ids_chunk,
                    base_mail_values,
                    additional_values={'body_html': mail_body}
                )
                new_email = SafeMail.create(mail_values)
                emails += new_email

        # NOTE:
        #   1. for more than 50 followers, use the queue system
        #   2. do not send emails immediately if the registry is not loaded,
        #      to prevent sending email during a simple update of the database
        #      using the command-line.
        test_mode = getattr(threading.current_thread(), 'testing', False)
        if force_send := self.env.context.get('mail_notify_force_send', force_send):
            force_send_limit = int(self.env['ir.config_parameter'].sudo().get_param('mail.mail.force.send.limit', 100))
            force_send = len(emails) < force_send_limit
        if force_send and (not self.pool._init or test_mode):
            # unless asked specifically, send emails after the transaction to
            # avoid side effects due to emails being sent while the transaction fails
            if not test_mode and send_after_commit:
                emails.send_after_commit()
            else:
                emails.send()

        return True
