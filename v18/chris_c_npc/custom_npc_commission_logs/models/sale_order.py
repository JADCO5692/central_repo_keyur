from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    subscription_pause_date = fields.Datetime(
        string='Subscription Paused On',
        compute='_compute_subscription_pause_date',
        store=False
    )

    @api.depends('message_ids')
    def _compute_subscription_pause_date(self):
        for order in self:
            order.subscription_pause_date = False

            # Search for field tracking messages related to 'subscription_state'
            messages = self.env['mail.message'].sudo().search([
                ('model', '=', 'sale.order'),
                ('res_id', '=', order.id),
                ('tracking_value_ids.field_id.name', '=', 'subscription_state')
            ], order='create_date asc')

            for msg in messages:
                for track in msg.tracking_value_ids:
                    if (
                        track.field_id.name == 'subscription_state' and
                        track.old_value_char == 'In Progress' and
                        track.new_value_char == 'Paused'
                    ):
                        order.subscription_pause_date = msg.create_date
                        break
                if order.subscription_pause_date:
                    break
        