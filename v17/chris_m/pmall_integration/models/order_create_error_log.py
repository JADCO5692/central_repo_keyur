from odoo import models, fields

class OrderCreateErrorLog(models.Model):
    _name = 'order.create.error.log'
    # create date desc

    name = fields.Char('Name')
    batch_id = fields.Char('Batch Id')
    partner_sku = fields.Char('Partner SKU')
    error_log = fields.Text('Error Log')
    order_number = fields.Char('Order Number')
    order_log_id = fields.Many2one('pmall.order.logs','Order Log')
    active = fields.Boolean("active",default=True)
    
    def unlink_old_logs(self, older_than=31):

        old_messages_date = fields.Datetime.to_string(
            datetime.now() - timedelta(days=older_than)
        )
        old_messages = self.with_context(active_test=False).search(
            [("create_date", "<", old_messages_date)]
        )
        old_messages.unlink()