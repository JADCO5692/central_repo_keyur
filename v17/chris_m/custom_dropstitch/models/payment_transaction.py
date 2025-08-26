from odoo import models, api


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _get_post_processing_values(self):
        res = super(PaymentTransaction, self)._get_post_processing_values()
        for transaction in self:
            if transaction.state == "done":
                move = self.env["account.move"].search(
                    [("name", "=", transaction.reference)]
                )
                if move:
                    order_id = move.line_ids.sale_line_ids.order_id
                    if order_id:
                        pickings = self.env["stock.picking"].search(
                            [("origin", "=", order_id.name)]
                        )
                        for picking in pickings:
                            if picking.state == "invoice_sent":
                                picking.state = "ready_to_be_sent"
                                if picking.batch_id:
                                    all_pickings = picking.batch_id.mapped(
                                        "picking_ids"
                                    ).filtered(
                                        lambda picking: picking.state
                                        not in ("cancel", "done")
                                    )
                                    ready_to_be_sent_pickings = picking.batch_id.mapped(
                                        "picking_ids"
                                    ).filtered(
                                        lambda picking: picking.state
                                        in ("ready_to_be_sent")
                                    )
                                    if len(all_pickings.ids) == len(
                                        ready_to_be_sent_pickings.ids
                                    ):
                                        picking.batch_id.state = "ready_to_be_sent"
                            if picking.state == "ready_to_be_sent":
                                if picking.batch_id:
                                    all_pickings = picking.batch_id.mapped(
                                        "picking_ids"
                                    ).filtered(
                                        lambda picking: picking.state
                                        not in ("cancel", "done")
                                    )
                                    ready_to_be_sent_pickings = picking.batch_id.mapped(
                                        "picking_ids"
                                    ).filtered(
                                        lambda picking: picking.state
                                        in ("ready_to_be_sent")
                                    )
                                    if len(all_pickings.ids) == len(
                                        ready_to_be_sent_pickings.ids
                                    ):
                                        picking.batch_id.state = "ready_to_be_sent"

        return res
