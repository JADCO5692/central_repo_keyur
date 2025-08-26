# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models
from datetime import datetime
from odoo.tools.misc import split_every

import logging

_logger = logging.getLogger(__name__)


class ShipstationInstanceEpt(models.Model):
    _inherit = "shipstation.instance.ept"

    def export_to_shipstation_cron(
        self, ctx={}, store_ids=False, start_date=False, end_date=False
    ):
        instance_id = ctx.get("shipstation_instance_id")
        instance = self.env["shipstation.instance.ept"].browse(instance_id)
        if not instance:
            return True
        domain = [
            "|",
            "&",
            "&",
            "&",
            "&",
            ("shipstation_instance_id", "=", instance.id),
            ("export_order", "=", True),
            ("is_exported_to_shipstation", "=", False),
            ("state", "=", "ready_to_be_sent"),
            ("exception_counter", "<=", 3),
            "&",
            "&",
            "&",
            "&",
            "&",
            ("shipstation_instance_id", "=", instance.id),
            ("export_order", "=", True),
            ("is_exported_to_shipstation", "=", False),
            ("state", "=", "assigned"),
            ("exception_counter", "<=", 3),
            ("custom_order_policy", "=", "products"),
        ]

        if store_ids:
            domain.append(("shipstation_store_id", "in", store_ids.ids))
        # if instance.shipstation_last_export_order and not start_date and end_date:
        #    domain.append(
        #        ('create_date', '>', instance.shipstation_last_export_order.strftime("%Y-%m-%d %H:%M:%S")))
        # elif start_date and end_date:
        if start_date and end_date:
            domain += [
                ("create_date", ">", start_date.strftime("%Y-%m-%d %H:%M:%S")),
                ("create_date", "<", end_date.strftime("%Y-%m-%d %H:%M:%S")),
            ]
        model_id = self.env["ir.model"].search([("model", "=", self._name)]).id
        log_line = self.env["common.log.lines.ept"]
        pickings = self.env["stock.picking"].search(domain, order="id desc")
        for picking in pickings:
            move_line_ids = picking._package_move_lines()
            if not move_line_ids:
                # if order is to fulfilled from shipstation and it is not exported
                try:
                    _logger.info("Exporting picking %s to shipstation - Instance", picking.name)
                    picking.with_context(
                        from_delivery_order=False
                    ).export_order_to_shipstation(log_line)
                except Exception as exception:
                    picking.unlink_old_message_and_post_new_message(body=exception)
                    msg = "Error : {} comes at the time of exporting order to Shipstation".format(
                        exception
                    )
                    log_line.create_common_log_line_ept(
                        message=msg,
                        model_id=model_id,
                        res_id=picking.id,
                        operation_type="export",
                        module="shipstation_ept",
                        log_line_type="fail",
                    )
                    _logger.exception(
                        "103: CRON ERROR while Exporting order %s to shipstation, \
                                    ERROR: %s",
                        picking.name,
                        exception,
                    )
                    continue
        if not start_date:
            instance.write({"shipstation_last_export_order": datetime.now()})
            
    def auto_validate_delivery_order(self, ctx={}):
        """
        Using the cronjob automatic validate the pickings
        """
        instance_id = ctx.get('shipstation_instance_id')
        instance = self.env['shipstation.instance.ept'].browse(instance_id)
        if not instance:
            _logger.info("No Shipstation Instance Found")
            return True
        pickings = self.env['stock.picking'].search(
            [('shipstation_instance_id', '=', instance.id), ('is_exported_to_shipstation', '=', True),
             ('picking_type_id.code', '=', 'outgoing'), ('state', '=', 'ready_to_be_sent')], order='id desc')
        _logger.info("Shipstation delivery orders list for auto validate: %s" % pickings.ids)
        for picking_batch in split_every(10, pickings):
            for picking in picking_batch:
                try:
                    wiz = picking.with_context(skip_sms=True).button_validate()
                except Exception as exception:
                    """ If Any Validation Error occur during Delivery Order Validation process then
                        activity will be created for that particular picking and also for all users 
                        which are configured in the instance.
                     """
                    activity = self.sudo().env['mail.activity']
                    is_activity_created = activity.search([('res_id','=',picking.id),
                                                           ('res_model','=','stock.picking')
                                                           ])
                    if not is_activity_created:
                        for user in instance.activity_user_ids:
                            activity_vals = self._prepare_activity_vals(picking=picking,instance=instance,note=exception,user=user)
                            activity.create(activity_vals)
                        _logger.info("Activity Created for picking ==> %s",picking.display_name)
                    continue

                # Immediate Transfer
                if wiz and isinstance(wiz, dict) and wiz.get('res_model', False) == 'stock.immediate.transfer':
                    try:
                        wiz = Form(self.env['stock.immediate.transfer'].with_context(wiz['context'])).save()
                        wiz = wiz.process()
                    except Exception as exception:
                        _logger.info("stock.immediate.transfer : Error {} comes at the time of "
                                     "validate picking : {}".format(exception, picking.id))
                        continue

                # Create Backorder
                if wiz and isinstance(wiz, dict) and wiz.get('res_model', False) == 'stock.backorder.confirmation':
                    try:
                        wiz = Form(self.env['stock.backorder.confirmation'].with_context(wiz['context'])).save()
                        wiz.process()
                        _logger.info("Shipstation backorder created from picking: %s" % picking.id)
                    except Exception as exception:
                        _logger.info("stock.backorder.confirmation : Error {} comes at the time of "
                                     "creating back order in picking : {}".format(exception, picking.id))
                        continue
                picking.find_outgoing_pickings_of_sale_order_and_export_to_shipstation()
                _logger.info("Shipstation delivery order process completed for auto validate: %s" % picking.id)
            self._cr.commit()
