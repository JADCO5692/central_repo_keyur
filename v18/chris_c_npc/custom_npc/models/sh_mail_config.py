# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime
import requests
import logging
_logger = logging.getLogger("debug_crm_message_post_flow")

class Office365BaseConfigInherit(models.Model):
    _inherit = 'sh.office365.base.config'

    def mail_import(self):
        self.RefreshToken()
        if self.auth_token and self.import_mail:
            try:
                get_mail_folders = "https://graph.microsoft.com/v1.0/me/messages?$select=bodyPreview,hasAttachments,receivedDateTime,sender,subject&$top=1000"
                headers = {
                                "Authorization": self.auth_token,
                                "Content-Type": "application/json"
                            }
                response = requests.get(url=get_mail_folders,headers=headers)
                res_json = response.json()
                values = res_json['value']
                for data in values:

                    sender_name = False
                    sender_email = False
                    if data.get('sender',False) and data.get('sender').get('emailAddress').get('address',False):

                        sender_name = data['sender']['emailAddress']['name']
                        sender_email = data['sender']['emailAddress']['address']

                    
                        subject = data['subject']
                        body = data['bodyPreview']
                        unique_id = data['id']
                        attachment = data['hasAttachments']
                        received_date = data['receivedDateTime']
                        dates = datetime.datetime.strptime(received_date,"%Y-%m-%dT%H:%M:%SZ")
                        domain = [('email', '=', sender_email)]
                        find_sender = self.env['res.partner'].search(domain,limit=1)
                        _logger.info(f"=======FOUND SENDER {find_sender.id}-{find_sender.name}=======")
                        vals = {
                            'model' : 'res.partner',
                            'subject' : subject,
                            'body' : body,
                            'unique_id' : unique_id,
                            'date' : dates,
                            'message_type' : 'email'
                        }
                        if attachment:
                            get_attachment = 'https://graph.microsoft.com/v1.0/me/messages/%s/attachments' %(unique_id)
                            resp_attachment = requests.get(url=get_attachment,headers=headers)
                            res_json_attachment = resp_attachment.json()
                            data = res_json_attachment['value']
                            for x in data:
                                if x.get('contentBytes',False):

                                    attach_bytes = x['contentBytes']
                                    name = x['name']
                                    content_type = x['contentType']
                                    attach_id = x['id']
                                    base64_bytes = attach_bytes.encode()
                                    ir_vals = {
                                        'name' : name,
                                        'type' : 'binary',
                                        'datas' : base64_bytes,
                                        'res_model' : 'res.partner',
                                        'attachment_id' : attach_id
                                    }
                                    if find_sender:
                                        vals['author_id'] = find_sender.id
                                        vals['res_id'] = find_sender.id
                                        ir_vals['res_id'] = find_sender.id
                                    else:
                                        create_vals = {
                                            'name' : sender_name,
                                            'email' : sender_email
                                        }
                                        create_instant_sender = self.env['res.partner'].create(create_vals)
                                        vals['author_id'] = create_instant_sender.id
                                        vals['res_id'] = create_instant_sender.id
                                        ir_vals['res_id'] = create_instant_sender.id
                                        domain = [('attachment_id','=',attach_id)]
                                        find_attachments = self.env['ir.attachment'].search(domain)
                                        if find_attachments:
                                            vals['attachment_ids'] = [(6,0,[find_attachments .id])]
                                        else:
                                            upload_attachment = self.env['ir.attachment'].create(ir_vals)
                                            vals['attachment_ids'] = [(6,0,[upload_attachment.id])]
                                    domain = [('unique_id', '=', unique_id)]
                                    find_mails = self.env['mail.message'].search(domain,limit=1)
                                    if find_mails:
                                        find_mails.write(vals)
                                    else:
                                        check = self.env['mail.message'].create(vals)
                                        _logger.info(f"=======CREATING MESSAGE WITH VALUES {vals} FOR PARTNER IF ATTACHMENT FOUND=======")
                                        _logger.info(f"=========CALLING CUSTOM METHOD find_crm_or_sub_message with values {sender_email} {vals} IF ATTACHMENT FOUND=======")
                                        self.find_crm_or_sub_message(sender_email, vals)
                        else:
                            if find_sender:
                                vals['author_id'] = find_sender.id
                                vals['res_id'] = find_sender.id
                            elif sender_name:
                                create_vals = {
                                    'name' : sender_name,
                                    'email' : sender_email
                                }
                                create_instant_sender = self.env['res.partner'].create(create_vals)
                                vals['author_id'] = create_instant_sender.id
                                vals['res_id'] = create_instant_sender.id
                            domain = [('unique_id', '=', unique_id)]
                            find_mails = self.env['mail.message'].search(domain,limit=1)
                            if find_mails:
                                find_mails.write(vals)
                            else:
                                check = self.env['mail.message'].create(vals)
                                _logger.info(
                                    f"=======CREATING MESSAGE WITH VALUES {vals} FOR PARTNER IF ATTACHMENT not FOUND=======")
                                _logger.info(
                                    f"=========CALLING CUSTOM METHOD find_crm_or_sub_message with values {sender_email} {vals} IF ATTACHMENT not FOUND=======")
                                self.find_crm_or_sub_message(sender_email, vals)
                        if self.manage_log_mail:
                            vals = {
                                "name" : self.name,
                                "state" : "success",
                                "error" : "Successully Done",
                                "base_config_id" : self.id,
                                "datetime" : datetime.datetime.now(),
                                "field_type" : "mail",
                                "operation" : "import"
                            }
                            self.env['sh.office365.base.log'].create(vals)
                    else:
                        vals = {
                            "name" : self.name,
                            "state" : "error",
                            "error" : "mail not found ",
                            "base_config_id" : self.id,
                            "datetime" : datetime.datetime.now(),
                            "field_type" : "mail",
                            "operation" : "import"
                        }
                        
                        self.env['sh.office365.base.log'].create(vals)

            except Exception as e:
                if self.manage_log_mail:
                    vals = {
                        "name" : self.name,
                        "state" : "error",
                        "error" : e,
                        "base_config_id" : self.id,
                        "datetime" : datetime.datetime.now(),
                        "field_type" : "mail",
                        "operation" : "import"
                    }
                    self.env['sh.office365.base.log'].create(vals) 
        else:
            raise UserError(_("Select Import to import mails"))

    def find_crm_or_sub_message(self, sender_email, vals):
        partner = self.env['res.partner'].search([('email', '=', sender_email)], limit=1)
        _logger.info(f"============FOUND SENDER IN CUSTOM METHOD{partner.id}-{partner.name}=======")
        crm_or_subscription = self.env['sale.order'].search(
            [('partner_id', '=', partner.id), ('plan_id', '!=', False)], limit=1)
        _logger.info(f"===========FOUND SUBSCRIPTION IN CUSTOM METHOD{crm_or_subscription.id}-{crm_or_subscription.name}========")
        if not crm_or_subscription:
            crm_or_subscription = self.env['crm.lead'].search(
                ['|', ('partner_id', '=', partner.id), ('email_from', '=', sender_email),
                 ('stage_id.name', 'not in', ['All Contracts signed', 'Paid Client'])], limit=1)
            _logger.info(
                f"===========FOUND CRM IN CUSTOM METHOD{crm_or_subscription.id}-{crm_or_subscription.name}-{crm_or_subscription.stage_id.name}========")
        if crm_or_subscription:
            vals['model'] = crm_or_subscription._name
            vals['res_id'] = crm_or_subscription.id
            if crm_or_subscription._name == 'crm.lead':
                vals['author_id'] = crm_or_subscription.user_id.partner_id.id
            elif crm_or_subscription._name == 'sale.order':
                vals['author_id'] = crm_or_subscription.user_id.partner_id.id
            _logger.info(f"=========CREATING MESSAGE FOR {crm_or_subscription._name}-{crm_or_subscription.id} WITH VALUES {vals}========")
            message_id = self.env['mail.message'].create(vals)
            _logger.info(f"============MESSAGE CREATED {message_id.id}-{message_id.read()}======")
        else:
            _logger.info(f"========NO SUBSCRIPTION OR CRM Found FOR {sender_email}- {partner.id}-{partner.name}=======")

