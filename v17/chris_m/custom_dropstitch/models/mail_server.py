from odoo import models, api


class MailMail(models.Model):
    _inherit = 'mail.message'

    @api.model
    def create(self, vals):
        # If related document is Shopify (SO/INV/DO with shopify_instance)
        model = vals.get('model')
        res_id = vals.get('res_id')
        if model and res_id:
            record = self.env[model].browse(res_id)
            if record.exists() and hasattr(record, 'shopify_instance_id') and model == 'account.payment':
                # If record has shopify_instance_id and it's set
                invoice = self.env['account.move'].search([('name', '=', record.ref)], limit=1)
                if invoice:
                    instance = invoice.shopify_instance_id
                    shopify_user = self.env['res.users'].search([('login', '=',instance.custom_emails)], limit=1)
                    # Force mail server
                    if instance and instance.mail_server_id:
                        vals['mail_server_id'] = instance.mail_server_id.id

                    # Force "From" address
                    if instance and instance.custom_emails:
                        vals['email_from'] = instance.custom_emails

                    if instance and shopify_user:
                        vals['author_id'] = shopify_user.partner_id.id
                    #
                    # if instance and instance.custom_reply_to:
                    #     vals['reply_to'] = instance.custom_reply_to

        return super(MailMail, self).create(vals)
