import logging
from odoo import models, fields, _
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_pmall_order = fields.Boolean('Is Pmall Order')
    pmall_order_log_id = fields.Many2one('pmall.order.logs','Pmall Order Log')
    pmall_order_number = fields.Char('Pmall Order Number')
    pmall_order_batch_number = fields.Char('Pmall Order Batch Number',related='pmall_order_log_id.batch_number')
    pmall_order_date = fields.Char('Pmall Order Date')
    pmall_config_id = fields.Many2one('pmall.config','Pmall Config Id',related="pmall_order_log_id.pmall_config_id")

    def process_order(self, date_order):
        self.ensure_one()
        try:
            self.action_confirm() 
            if date_order:
                self.date_order = date_order
            invoice = (
                self.env["sale.advance.payment.inv"]
                .with_context(
                    {
                        "active_model": "sale.order",
                        "active_id": self.id,
                    }
                )
                .create(
                    {
                        "advance_payment_method": "delivered",
                    }
                )
                ._create_invoices(self)
            )
            invoice.action_post()
        except Exception as err:
            _logger.info("Error when BOM product explode: %s", err) 