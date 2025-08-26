import binascii
import json
import logging
import base64, os, tempfile
from markupsafe import Markup
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form
from PyPDF2 import PdfFileMerger

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    """
    inheriting stock.picking for implementation of ShipStation.
    """
    _inherit = 'stock.picking'
    _description = 'Stock Picking'

    shipstation_instance_id = fields.Many2one('shipstation.instance.ept', string='Instance')
    shipstation_store_id = fields.Many2one('shipstation.store.ept', string='Shipstation Store')
    shipstation_order_id = fields.Char(string='Shipstation Order Reference', copy=False)
    shipstation_shipment_id = fields.Char("Shipment ID", help="Shipstation Shipment ID", copy=False)
    shipstation_carrier_id = fields.Many2one('shipstation.carrier.ept', store=True)
    shipstation_service_id = fields.Many2one('shipstation.services.ept', string='Shipstation Service')
    shipstation_package_id = fields.Many2one('stock.package.type', string='Shipstation Package')
    delivery_rate_ids = fields.One2many('delivery.rate.ept', 'picking_id', string='Delivery Rates', copy=False)
    shipping_rates = fields.Float(string='Shipping Rate', copy=False)
    is_exported_to_shipstation = fields.Boolean("Exported to shipstation?", copy=False, default=False)
    is_get_shipping_label = fields.Boolean('Is Shipping Label Available?', copy=False, default=False)
    marked_as_shipped_to_shipstation = fields.Boolean("Marked as Shipped", copy=False, default=False)
    canceled_on_shipstation = fields.Boolean(string="Cancelled on shipstation?", copy=False, default=False)
    export_order = fields.Boolean(string='Export order to Shipstation?', default=False)
    confirmation = fields.Selection(
        [('none', 'None'),
         ('delivery', 'Delivery'),
         ('signature', 'Signature'),
         ('adult_signature', 'Adult Signature'),
         ('direct_signature', 'Direct Signature')],
        default="none", copy=False)
    is_residential = fields.Boolean("Is Residential", default=False)
    shipstation_send_to_shipper_process_done = fields.Boolean('Shipstation Send To Shipper (Done).', copy=False,
                                                              readonly=True,
                                                              help="This field indicates that send to shipper "
                                                                   "for picking is done.")
    shipstaion_actual_shipping_cost = fields.Float(string="Shipstation Actual Shipping cost")
    related_outgoing_picking = fields.Many2one("stock.picking", string="Related Outgoing Picking")
    exported_order_to_shipstation = fields.Char('Exported order to shipstation')
    validated_shipstation_order_id = fields.Char('Validated Shipstation OrderId', copy=False)
    exception_counter = fields.Integer(string="Counter", default=0)
    contents_of_international_shipment = fields.Selection([('merchandise', 'Merchandise'),
                                                           ('documents', 'Documents'),
                                                           ('gift', 'Gift'),
                                                           ('returned_goods', 'Returned Goods'),
                                                           ('sample', 'Sample')],
                                                          string="Contents of International Shipment",
                                                          help="Contents of International Shipment by ShipStation")
    non_delivery_option = fields.Selection([('return_to_sender', 'Return to Sender'),
                                            ('treat_as_abandoned', 'Treat as Abandoned')],
                                           string="Non-Delivery Option",
                                           help="Non-Delivery option for International Shipment by ShipStation")

    def get_default_uom_ept(self):
        """ Add default weight uom to the Stock Picking
            @return: return default weight uom id
        """
        company_id = self.company_id or self.env.user.company_id
        if company_id and company_id.get_weight_uom_id():
            return company_id.get_weight_uom_id()

        weight_uom_id = self.env.ref('uom.product_uom_kgm', raise_if_not_found=False)
        if not weight_uom_id:
            uom_categ_id = self.env.ref('uom.product_uom_categ_kgm').id
            weight_uom_id = self.env['uom.uom'].search(
                [('category_id', '=', uom_categ_id), ('factor', '=', 1)],
                limit=1)
        return weight_uom_id

    shipstation_weight_uom_id = fields.Many2one('uom.uom', string='Shipstation Unit of Measure', required=True,
                                                domain=lambda self: [('category_id.id', '=',
                                                                      self.env.ref('uom.product_uom_categ_kgm').id)],
                                                help="Unit of measurement for Weight", default=get_default_uom_ept)

    def default_get(self, fields):
        """
        inherited method to update the shipment id
        """
        res = super(StockPicking, self).default_get(fields)
        if self.shipstation_instance_id:
            res['contents_of_international_shipment'] = self.shipstation_instance_id.contents_of_international_shipment
            res['non_delivery_option'] = self.shipstation_instance_id.non_delivery_option
        return res

    @api.onchange('shipstation_instance_id')
    def onchange_shipstation_instance_id(self):
        """
        Onchange method for shipstation_instance_id
        """
        if self.shipstation_store_id.shipstation_instance_id.id != self.shipstation_instance_id.id:
            self.shipstation_store_id = False
        self.contents_of_international_shipment = self.shipstation_instance_id.contents_of_international_shipment
        self.non_delivery_option = self.shipstation_instance_id.non_delivery_option

        if not self.carrier_id.get_cheapest_rates:
            self.shipstation_service_id = self.carrier_id.shipstation_service_id or False
        else:
            if len(self.carrier_id.shipstation_service_ids) == 1:
                self.shipstation_service_id = self.carrier_id.shipstation_service_ids or False
            else:
                self.shipstation_service_id = False

    @api.onchange('carrier_id')
    def onchange_shipstation_carrier_id(self):
        """
        OnChange method for carrier_id
        """
        self.shipstation_instance_id = self.carrier_id.shipstation_instance_id.id or False
        self.shipstation_package_id = self.carrier_id.shipstation_package_id.id or False
        self.confirmation = self.carrier_id.confirmation
        self.is_residential = self.carrier_id.is_residential_address

        if not self.carrier_id.get_cheapest_rates:
            self.shipstation_carrier_id = self.carrier_id.shipstation_carrier_id or False
            self.shipstation_service_id = self.carrier_id.shipstation_service_id or False
        else:
            if len(self.carrier_id.shipstation_carrier_ids.ids) == 1:
                self.shipstation_carrier_id = self.carrier_id.shipstation_carrier_ids or False
            else:
                self.shipstation_carrier_id = False
            if len(self.carrier_id.shipstation_service_ids) == 1:
                self.shipstation_service_id = self.carrier_id.shipstation_service_ids or False
            else:
                self.shipstation_service_id = False

    def button_validate(self):
        """
            Inheriting button_validate to check for tracking if order is exported or originally from shipstation.
            or else send the tracking back to shipstation if the order is fulfilled in odoo.
        """
        for picking in self:
            # In case of validate internal picking:
            # If order already exported to ShipStation and Shipped Partially then create backorder
            if picking.picking_type_id.code == 'internal' and picking.sale_id.shipstation_instance_id and picking.is_order_pick_ship():
                outgoing_pickings = self.find_outgoing_picking()
                for out_picking in outgoing_pickings:
                    result = out_picking.check_is_order_shipped_and_create_back_order()
                    if not result:
                        msg = _("Something went wrong while validating the picking: %s", out_picking._get_html_link())
                        picking.message_post(body=msg)
                        self -= picking

            # When order is to be exported to ShipStation, But it is still not exported to Shipstation
            # then it will post a message and will skip this picking.
            if picking.shipstation_instance_id and picking.export_order and not picking.is_exported_to_shipstation:
                msg = "Cannot Validate {}, as order is pending to be export to ShipStation".format(picking.name)
                picking.unlink_old_message_and_post_new_message(body=msg)
                if picking.batch_id:
                    picking.batch_id.unlink_old_message_and_post_new_message(body=msg)
                self -= picking
                continue

            # Check for status and fetch tracking number from shipstation:
            if (
                    picking.shipstation_order_id or picking.exported_order_to_shipstation) and picking.shipstation_instance_id:
                result, response = picking.find_if_shipped_and_fetch_tracking_number()
                if not result:
                    self -= picking
                    continue

        res = super(StockPicking, self).button_validate()

        for picking in self.filtered(lambda x: x.state == "done" and x.picking_type_id.code == "internal"):
            if len(self) > 1:
                picking.with_context(from_delivery_order=False).find_related_outgoing_picking_and_export()
            else:
                picking.find_related_outgoing_picking_and_export()

        self.sudo().delivery_rate_ids.unlink()
        return res

    def find_if_shipped_and_fetch_tracking_number(self):
        """
        - Call API for checked order is shipped in ShipStation if Yes then get Tracking details.
        - If order get split in shipstation then create the backorder based on its orderStatus and done qty.
        """
        instance = self.shipstation_instance_id
        tracking_number = ''
        shipping_cost = 0
        # For backorder find first picking export order name to get order response from shipstation.
        order_number = self.prepare_export_order_name() if not self.exported_order_to_shipstation else self.exported_order_to_shipstation
        url = '/orders'
        querystring = {'orderNumber': order_number}
        response, code = instance.get_connection(url=url, data=None, params=querystring, method="GET")

        if code.status_code != 200:
            try:
                res = json.loads(code.content.decode('utf-8')).get('ExceptionMessage')
            except:
                res = code.content.decode('utf-8')
            msg = "While requesting for order status of {} on shipstation: {}".format(self.name, res)
            self.unlink_old_message_and_post_new_message(body=msg)
            _logger.info(msg)
            return False, response

        if len(response.get('orders')) > 1:
            # Checked all orders are in waiting state then directly return from here & send message.
            check_order_status_waiting = all(
                res.get('orderStatus') == 'awaiting_shipment' for res in response.get('orders'))
            if check_order_status_waiting:
                self.unlink_old_message_and_post_new_message(body="Order has not been shipped on the shipstation.")
                _logger.info("Order: %s has not been shipped on the shipstation.", self.name)
                return False, response

            # Checked all orders are in cancel state then cancel picking order from here.
            check_order_status_cancel_all = all(res.get('orderStatus') == 'cancelled' for res in response.get('orders'))
            if check_order_status_cancel_all:
                self.action_cancel()
                return False, response

            # From response set sorting to set shipped order first & execute it first.
            order_number_response = sorted(response.get('orders'), key=lambda d: d['orderStatus'] != 'shipped')
            for response_val in order_number_response:
                # Checked that picking already validated or not.
                exist_bo_id = self.env['stock.picking'].search([
                    ('validated_shipstation_order_id', '=', response_val.get('orderId'))])
                if not exist_bo_id and not self.validated_shipstation_order_id:
                    if response_val.get('orderStatus', '') == 'shipped' and self.state == 'assigned':
                        self.is_get_shipping_label = True
                        for back_line in self.move_ids:
                            is_item_in_responce = False
                            for item in response_val.get('items'):
                                if item.get('sku', '') == back_line.product_id.default_code:
                                    is_item_in_responce = True
                                    back_line.write({
                                        'quantity': item.get('quantity'),
                                        'picked': True
                                    })
                                    if not self.validated_shipstation_order_id:
                                        self.write({
                                            'validated_shipstation_order_id': response_val.get('orderId'),
                                            'shipstation_order_id': response_val.get('orderId')
                                        })
                            if not is_item_in_responce:
                                back_line.write({'quantity': 0})
                        # Get Tracking Reference
                        ship_url = '/shipments?orderId=%s' % response_val.get('orderId', False)
                        shipment_response, code = instance.get_connection(url=ship_url, data=None, params=None, method="GET")
                        if code.status_code != 200:
                            try:
                                res = json.loads(code.content.decode('utf-8')).get(
                                    'ExceptionMessage')
                            except:
                                res = code.content.decode('utf-8')
                            msg = 'While requesting for tracking number of %s on Shipstation: %s' % (self.name, res)
                            self.unlink_old_message_and_post_new_message(body=msg)
                            _logger.exception(msg)
                            return False, shipment_response

                        if self.sale_id.team_id.shipstation_update_carrier:
                            self.set_carrier_based_on_response(shipment_response)

                        for shipment in shipment_response.get('shipments'):
                            if str(shipment.get('voided', '')).lower() == 'true':
                                continue
                            tracking_number = shipment.get('trackingNumber', False)
                            shipping_cost += shipment.get('shipmentCost', 0)
                            if self.shipstation_order_id:
                                self.shipstation_order_id = response_val.get('orderId')
                    elif response_val.get('orderStatus') == 'cancelled':
                        check_order_status_waiting_any = any(
                            res.get('orderStatus') == 'awaiting_shipment' for res in response.get('orders'))
                        # Checked if any other order still in waiting state in shipstation then
                        # return from here & send message.
                        if check_order_status_waiting_any:
                            self.unlink_old_message_and_post_new_message(
                                body="Label has not been generated on the shipstation.")
                            _logger.info(
                                "Label has not been generated on the shipstation for picking:"
                                " %s", self.name)
                            return False, response
                        cancel_status = self.action_cancel()
                        # If cancel process succeed then update shipstation order id value.
                        if cancel_status:
                            self.write({'shipstation_order_id': response_val.get('orderId')})
                        return False, response
                    elif not self.validated_shipstation_order_id:
                        self.unlink_old_message_and_post_new_message(
                            body="Label has not been generated on the shipstation.")
                        _logger.info("Label has not been generated on the shipstation for picking:"
                                     " %s", self.name)
                        return False, response
        elif len(response.get('orders')) == 1:
            """
            Modify By - Vaibhav Chadaniya
            15556: Avoid duplicate call & Get shipstation order id from response (In Single Order Case)
            Remove the duplicate call to retrieve the order from the initial API response.
            """
            response_order = response.get('orders')[0]
            if code.status_code != 200:
                try:
                    res = json.loads(code.content.decode('utf-8')).get('ExceptionMessage')
                except:
                    res = code.content.decode('utf-8')
                msg = "While requesting for order status of {} on shipstation: {}".format(
                    self.name, res)
                self.unlink_old_message_and_post_new_message(body=msg)
                if self.batch_id:
                    self.batch_id.unlink_old_message_and_post_new_message(
                        body="While requesting for order status of {} on shipstation: {}".format(
                            self.name, res))
                _logger.info(msg)
                return False, response

            if response_order.get('orderStatus') == 'cancelled':
                self.action_cancel()
                return False, response

            if not response_order.get('orderStatus') == 'shipped':
                self.unlink_old_message_and_post_new_message(body="Label has not been generated on the shipstation.")
                if self.batch_id:
                    self.batch_id.unlink_old_message_and_post_new_message(
                        body="Label has not been generated for {} on the shipstation.".format(self.name))
                _logger.info("Label has not been generated on the shipstation for picking: %s", self.name)
                return False, response

            self.is_get_shipping_label = True
            url = '/shipments?orderId=%s' % response_order.get('orderId', self.shipstation_order_id)
            response, code = instance.get_connection(url=url, data=None, params=None, method="GET")
            if code.status_code != 200:
                try:
                    res = json.loads(code.content.decode('utf-8')).get('ExceptionMessage')
                except:
                    res = code.content.decode('utf-8')
                msg = 'While requesting for Tracking number of %s on Shipstation' \
                      '\n%s' % (self.name, res)
                self.unlink_old_message_and_post_new_message(body=msg)
                if self.batch_id:
                    self.batch_id.unlink_old_message_and_post_new_message(body=msg)
                _logger.exception(msg)
                return False, response

            if self.sale_id.team_id.shipstation_update_carrier:
                self.set_carrier_based_on_response(response)

            for shipment in response.get('shipments'):
                if str(shipment.get('voided', '')).lower() == 'true':
                    continue
                tracking_number += ', {}'.format(
                    shipment.get('trackingNumber', '')) if tracking_number else shipment.get('trackingNumber', '')
                shipping_cost += shipment.get('shipmentCost', 0)
        else:
            msg = "While requesting for order {} not found on shipstation".format(self.name)
            self.unlink_old_message_and_post_new_message(body=msg)
            return False, response
        shipping_cost = self.convert_company_currency_amount_to_order_currency(shipping_cost)
        self.write({
            'carrier_tracking_ref': tracking_number,
            'shipstaion_actual_shipping_cost': shipping_cost
        })
        return True, response

    def get_package_dimension(self):
        _logger.info("here 0a=================")
        if len(self.package_ids) == 1:
            _logger.info("here 0b=================")
            package_dimension_data = self.package_ids.package_type_id
        else:
            _logger.info("here 0c=================")
            if self.shipstation_package_id:
                _logger.info("here 0d=================")
                package_dimension_data = self.shipstation_package_id
            else:
                _logger.info("here 0e=================")
                package_dimension_data = self.carrier_id.shipstation_package_id
        _logger.info(package_dimension_data)
        _logger.info("here 0f=================")
        return package_dimension_data

    def prepare_dimensions_data(self, data, package, package_unit_default, package_code=False):
        """
        Add package dimensions to the request data.
        """

        _logger.info("here 1b=================")
        _logger.info(package.packaging_length)
        _logger.info("here 1c=================")
        _logger.info(package.width)
        _logger.info("here 1d=================")
        _logger.info(package.height)
        _logger.info("here 1e=================")
        _logger.info(package)
        _logger.info("here 1f=================")
        if package.width > 0 and package.height > 0:
            data.update({
                "dimensions": {
                    "length": package.packaging_length,
                    "width": package.width,
                    "height": package.height,
                    "units": package_unit_default
                }
            })
            """
            Added carrier default_package_id configuration to make package code carrier dependent
            """
            if package_code:
                data.update({"packageCode": package_code})

        return data

    def get_rates(self):
        """
        This method is to get the rates of shipment for Delivery Order
        """
        if not self.carrier_id:
            raise UserError('Please set delivery method in Delivery Order!')

        if not self.shipstation_instance_id:
            raise UserError('Please set delivery method in Delivery order!')

        shipstation_warehouse = self.env['shipstation.warehouse.ept'].search(
            ['|', ('odoo_warehouse_id', '=', self.picking_type_id.warehouse_id.id),
             ('is_default', '=', True),
             ('shipstation_instance_id', '=', self.shipstation_instance_id.id)], limit=1)
        if not shipstation_warehouse:
            msg = 'Ship-station warehouse must be selected in the current Ship-station store.'
            raise UserError(msg)

        try:
            total_weight = self.get_converted_weight_for_shipstation()
        except Exception as e:
            raise UserError(e)

        instance = self.shipstation_instance_id
        shipstation_service_obj = self.env['shipstation.services.ept']
        delivery_rate_obj = self.env['delivery.rate.ept']
        shipping_partner_id = self.partner_id
        data = {}
        rate_for_service_not_found = []

        if len(self.package_ids) == 1:
            package_code = self.package_ids.package_type_id.shipper_package_code
        else:
            package_code = self.shipstation_package_id.shipper_package_code or self.carrier_id.shipstation_package_id.shipper_package_code or 'package'

        shipstation_carriers = self.carrier_id.shipstation_carrier_id
        if self.carrier_id.get_cheapest_rates:
            shipstation_carriers = self.carrier_id.shipstation_carrier_ids
        else:
            if self.shipstation_service_id:
                data.update({"serviceCode": self.shipstation_service_id.service_code})
            else:
                data.update({"serviceCode": self.carrier_id.shipstation_service_id.service_code})

        if not shipstation_carriers:
            msg = 'No ShipStation Carrier Found on Delivery Carrier %s' % self.carrier_id.name
            raise UserError(msg)

        package = self.get_package_dimension()

        self.delivery_rate_ids.unlink()
        for carrier in shipstation_carriers:
            data.update({
                "carrierCode": carrier.code,
                "packageCode": package_code,
                "fromPostalCode": shipstation_warehouse.origin_address_id.zip,
                "toState": shipping_partner_id.state_id.code,
                "toCountry": shipping_partner_id.country_id.code,
                "toPostalCode": shipping_partner_id.zip,
                "toCity": shipping_partner_id.city,
                "weight": {
                    "value": total_weight,
                    "units": self.shipstation_instance_id.shipstation_weight_uom
                },
                "confirmation": self.confirmation,
                "residential": self.is_residential,
            })

            self.prepare_dimensions_data(data, package, self.carrier_id.package_unit_default, carrier.default_package_id.shipper_package_code)

            """
            Pass (fromCity,fromState,fromWarehouseId) parameters in get rate API if available.
            """
            if shipstation_warehouse.origin_address_id.city:
                data.update({"fromCity": shipstation_warehouse.origin_address_id.city})
            if shipstation_warehouse.origin_address_id.state_id.code:
                data.update({"fromState": shipstation_warehouse.origin_address_id.state_id.code})
            if shipstation_warehouse.shipstation_identification:
                data.update({"fromWarehouseId": str(shipstation_warehouse.shipstation_identification)})

            response, code = instance.get_connection(url='/shipments/getrates', data=data, method="POST")
            if code.status_code != 200:
                try:
                    res = json.loads(code.content.decode('utf-8')).get('ExceptionMessage')
                except:
                    res = code.content.decode('utf-8')
                # Error Code 104
                self.unlink_old_message_and_post_new_message(body='104: %s' % res)
                _logger.exception('104: %s While get rates for Picking %s and Carrier %s', res, self.name, carrier.name)
                raise UserError("104: %s" % res)
            if not response:
                rate_for_service_not_found.append(carrier)
            selected_services = self.carrier_id.shipstation_service_ids.filtered(
                lambda x: x.shipstation_carrier_id.id == carrier.id).mapped('service_code')
            for res in response:
                if self.carrier_id.get_cheapest_rates and selected_services:
                    if res.get('serviceCode', False) not in selected_services:
                        continue
                shipping_cost = self.convert_company_currency_amount_to_order_currency(res.get('shipmentCost', 0))
                other_cost = self.convert_company_currency_amount_to_order_currency(res.get('otherCost', 0))
                service_name = res.get('serviceName', False)
                service_id = shipstation_service_obj.search([('service_code', '=', res.get('serviceCode', False)),
                                                             ('shipstation_carrier_id', '=', carrier.id)])
                if not service_id:
                    continue

                delivery_rate = delivery_rate_obj.search([('picking_id', '=', self.id),
                                                          ('shipstation_carrier_id', '=', carrier.id),
                                                          ('service_id', '=', service_id.id),
                                                          ('shipment_cost', '=', shipping_cost),
                                                          ('other_cost', '=', other_cost),
                                                          ('service_name', '=', service_name)])
                if delivery_rate:
                    continue
                total_cost = other_cost + shipping_cost
                if total_cost > 0:
                    rate_vals = {
                        'picking_id': self.id,
                        'shipstation_carrier_id': carrier.id or False,
                        'service_id': service_id.id or False,
                        'shipment_cost': shipping_cost or False,
                        'other_cost': other_cost or False,
                        'service_name': service_name or False,
                        'package_code': package_code or False
                    }
                    delivery_rate_obj.create(rate_vals)

        if not self.delivery_rate_ids:
            raise UserError('105: No rates are available for Picking {}'.format(self.name))
        return True

    def export_order_to_shipstation(self, log_line=False):
        """
            This method is used to export the orders to shipstation.
        """
        if self.state != 'assigned':
            raise UserError("Picking {} must be in ready state for export order to shipstation.".format(self.name))
        # if not self.carrier_id:
        #     raise UserError("Need to select Carrier in Picking for export order to shipstation.")
        self.is_picking_contains_store()

        model_id = self.env['ir.model'].sudo().search([('model', '=', self._name)]).id

        total_amount, tax_amount, shipping_amount, shipping_tax = 0, 0, 0, 0
        shipstation_instance = self.shipstation_store_id.shipstation_instance_id
        shipping_line = self.sale_id.order_line.filtered(lambda x: x.is_delivery)
        order_data = self.prepare_order_export_data()
        msg = isinstance(order_data, str) and order_data or ''

        exported_picking = self.get_exported_pickings()
        if not exported_picking:
            shipping_amount = self.convert_amount_to_company_currency(sum(shipping_line.mapped('price_subtotal')))
            shipping_tax = self.convert_amount_to_company_currency(sum(shipping_line.mapped('price_tax')))

        # Prepare order lines data
        process_lines = []
        line_list = []
        for line in self.move_ids.filtered(lambda move: move.quantity > 0):
            sale_line = line.sale_line_id
            line_data, sale_total_data = self.prepare_line_export_data(sale_line, move_id=line,
                                                                       process_lines=process_lines)

            msg += isinstance(line_data, str) and not sale_total_data and line_data or ''
            if msg:
                if self.exception_counter >= 3 and self._context.get('from_cron'):
                    self.message_post(body='Export Order Cron Failed as Exception has already '
                                           'been generated for 3 times while Processing this Picking.')
                else:
                    self.message_post(
                        body='Following parameters are missing, when order exported to shipstation: ' + msg)

                if self._context.get('from_cron'):
                    self.exception_counter += 1
                return

            if not line_data:
                return False
            process_lines.append(sale_line.id)
            line_list += line_data
            line.write({'shipstation_exported_qty': line.quantity})
            total_amount += sale_total_data.get('total', 0)
            tax_amount += sale_total_data.get('tax', 0)

        order_data.update({
            "orderStatus": "awaiting_shipment",
            "amountPaid": total_amount + shipping_tax + shipping_amount + tax_amount,
            "taxAmount": tax_amount + shipping_tax,
            "shippingAmount": shipping_amount,
            'items': line_list,
            'requestedShippingService': self.carrier_id.shipstation_carrier_code or self.carrier_id.name
        })
        response, code = shipstation_instance.get_connection(url='/orders/createorder', data=order_data, method="POST")
        if code.status_code != 200:
            try:
                res = json.loads(code.content.decode('utf-8')).get('ExceptionMessage')
            except:
                res = code.content.decode('utf-8')

            msg = "106: Something went wrong while exporting order to ShipStation.\n\n %s", res
            _logger.exception(msg)
            if not self._context.get('from_delivery_order', True):
                if self.exception_counter >= 3 and self._context.get('from_cron'):
                    self.message_post(body='Export Order Cron Failed as Exception has already '
                                           'been generated for 3 times while Processing this Picking.')
                else:
                    self.message_post(body=msg)

                if self._context.get('from_cron'):
                    self.exception_counter += 1
                return
            else:
                raise UserError(msg)

        msg = ("Order exported to ShipStation." + Markup("<br/>") +
               "ShipStation order id : %s" % (response.get('orderId')))
        self.unlink_old_message_and_post_new_message(body=msg)
        self.write({'shipstation_order_id': response.get('orderId'), 'is_exported_to_shipstation': True})

        # Update related outgoing picking in case of Multi-Step Routes
        is_multi_step = True if self.picking_type_id.warehouse_id.delivery_steps in (
            'pick_ship', 'pick_pack_ship') else False
        if is_multi_step:
            int_picks = self.get_internal_pickings()
            int_picks.write({'related_outgoing_picking': self.id})
        log_line = self.env['common.log.lines.ept']
        log_line.create_common_log_line_ept(message="Order Exported successfully", operation_type='export',
                                            model_id=model_id, res_id=self.id,
                                            module='shipstation_ept', log_line_type='success')
        return True

    def generate_multiple_label_on_shipstation(self):
        for picking in self:
            if not picking.shipstation_instance_id:
                raise ValidationError(_("Delivery order %s is not having shipstation order.", picking.name))
            if picking.state != "done" or picking.picking_type_id.code != "outgoing" or picking.is_get_shipping_label:
                raise ValidationError(_("Delivery order %s is not valid for Generate Label.", picking.name))
            picking.get_shipstation_label()

        _logger.info("Label Generation Start!!!!!! %s" % fields.Datetime.now())
        attachment_id, batch_file_name = self.download_label()
        _logger.info("Label Generation END!!!!!! %s" % fields.Datetime.now())
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment_id.id,
            'target': 'new',
            'nodestroy': False,
        }

    def download_label(self):
        """
        Create/Update PDF with all picking labels
        :return:
        """
        attachments = self.env['ir.attachment']
        f2_name_list = []
        for transfer_id in self:
            attachments_ids = attachments.search(
                [('res_model', '=', 'stock.picking'), ('res_id', 'in', [transfer_id.id]), ('name', 'ilike', 'Label')],
                order='id desc')
            count = 1
            if not attachments_ids:
                raise ValidationError(_("Label not generated against the shipment %s", transfer_id.name))
            for rec in attachments_ids:
                file_name = rec.res_name.replace('/', '_') + '_' + str(count) + '.pdf'
                f2_name = os.path.join(tempfile.gettempdir(),
                                       file_name)
                f2_name_list.append(f2_name)
                pre_f = base64.b64decode(
                    rec.datas)
                with open(f2_name, 'wb') as f1:
                    f1.write(pre_f)
                    f1.close()
                count += 1
        batch_file_name = 'Shipstation_Labels_%s.pdf' % datetime.now().strftime("%Y%m%d%H%M%S")
        f1_name = os.path.join(tempfile.gettempdir(), batch_file_name)
        with open(f1_name, 'wb') as f:
            f.write(b'')
            f.close()
        output_pdf = self.merge_pdfs(f2_name_list, f1_name)
        cf = open(output_pdf, 'rb')
        attachment_dict = {
            'name': batch_file_name,
            'datas': base64.b64encode(cf.read()),
            'res_model': self._name,
            # 'res_id': rec.id,
            'type': 'binary',
        }
        attachment_id = attachments.sudo().create(attachment_dict)
        # Remove Temp files form directory
        if output_pdf:
            os.remove(os.path.join(tempfile.gettempdir(), output_pdf))
        for f_name in f2_name_list:
            os.remove(os.path.join(tempfile.gettempdir(), f_name))
        return [attachment_id, batch_file_name]

    def merge_pdfs(self, input_pdfs, output_pdf):
        """Combine multiple pdfs to single pdf.
        Args:
            input_pdfs (list): List of path files.
            output_pdf (str): Output file.

        """
        pdf_merger = PdfFileMerger()
        for path in input_pdfs:
            pdf_merger.append(path, import_bookmarks=False)
        with open(output_pdf, 'wb') as fileobj:
            pdf_merger.write(fileobj)
            pdf_merger.close()
        return output_pdf

    def get_shipstation_label(self):
        carrier_id = self.shipstation_service_id.shipstation_carrier_id
        instance = self.shipstation_instance_id
        ship_date = self.date_done.strftime("%Y-%m-%d")
        warehouse = self.picking_type_id.warehouse_id
        # self.is_picking_contains_service_and_package()
        ship_from_partner = warehouse.partner_id
        ship_to_partner = self.partner_id
        # if Shipping Label Put In Pack wise configuration is true
        if self.shipstation_instance_id.is_shipping_label_package_wise and self.package_ids:
            shipping_data=self.get_shipstation_label_package_wise(carrier_id, instance, ship_date, warehouse, ship_from_partner,ship_to_partner)
            return shipping_data
        else:
            total_weight = self.get_converted_weight_for_shipstation()
            context = self._context.get('from_delivery_order', True)
            msg = ''
            if not total_weight:
                data_string = "Weight is not set"
                if not context:
                    msg += Markup("<br/>") + '- ' + data_string
                else:
                    raise UserError("{} in Picking : {}".format(data_string, self.name))
            if not carrier_id.code:
                data_string = "Carrier code is not set"
                if not context:
                    msg += Markup("<br/>") + '- ' + data_string
                else:
                    raise UserError("{} in Picking : {}".format(data_string, self.name))
            if not self.shipstation_service_id.service_code:
                data_string = "Service code is not set"
                if not context:
                    msg += Markup("<br/>") + '- ' + data_string
                else:
                    raise UserError("{} in Picking : {}".format(data_string, self.name))
            if not self.shipstation_package_id.shipper_package_code:
                data_string = "Package code is not set"
                if not context:
                    msg += Markup("<br/>") + '- ' + data_string
                else:
                    raise UserError("{} in Picking : {}".format(data_string, self.name))
            if not ship_from_partner.zip:
                data_string = "Postal Code in sender address is not set"
                if not context:
                    msg += Markup("<br/>") + '- ' + data_string
                else:
                    raise UserError("{} in Picking : {}".format(data_string, self.name))
            if ship_from_partner.country_id:
                if not ship_from_partner.country_id.code:
                    data_string = "Country code in sender address is not set"
                    if not context:
                        msg += Markup("<br/>") + '- ' + data_string
                    else:
                        raise UserError("{} in Picking : {}".format(data_string, self.name))
            else:
                data_string = "Country name in sender address is not set"
                if not context:
                    msg += Markup("<br/>") + '- ' + data_string
                else:
                    raise UserError("{} in Picking : {}".format(data_string, self.name))
            if not ship_to_partner.name:
                data_string = "Delivery partner name is not set"
                if not context:
                    msg += Markup("<br/>") + '- ' + data_string
                else:
                    raise UserError("{} in Picking : {}".format(data_string, self.name))
            if not ship_to_partner.street:
                data_string = "Street in delivery partner address is not set"
                if not context:
                    msg += Markup("<br/>") + '- ' + data_string
                else:
                    raise UserError("{} in Picking : {}".format(data_string, self.name))
            if not ship_to_partner.zip:
                data_string = "Postal code in delivery partner address is not set"
                if not context:
                    msg += Markup("<br/>") + '- ' + data_string
                else:
                    raise UserError("{} in Picking : {}".format(data_string, self.name))
            if ship_to_partner.country_id:
                if not ship_to_partner.country_id.code:
                    data_string = "Country code in delivery partner address is not set"
                    if not context:
                        msg += Markup("<br/>") + '- ' + data_string
                    else:
                        raise UserError("{} in Picking : {}".format(data_string, self.name))
            else:
                data_string = "Country name in delivery partner address is not set"
                if not context:
                    msg += Markup("<br/>") + '- ' + data_string
                else:
                    raise UserError("{} in Picking : {}".format(data_string, self.name))

            if ship_to_partner.country_id and warehouse.partner_id.country_id and ship_to_partner.country_id.id != warehouse.partner_id.country_id.id:
                if not self.contents_of_international_shipment:
                    data_string = "Contents of International Shipment option is not set"
                    if not context:
                        msg += '<br>' + '- ' + data_string
                    else:
                        raise UserError("{} in Picking : {}".format(data_string, self.name))

                if not self.non_delivery_option:
                    data_string = "Non-Delivery option is not set"
                    if not context:
                        msg += '<br>' + '- ' + data_string
                    else:
                        raise UserError("{} in Picking : {}".format(data_string, self.name))

            if msg:
                return msg

            package = self.get_package_dimension()

            data = {
                "carrierCode": carrier_id.code,
                "serviceCode": self.shipstation_service_id.service_code,
                "packageCode": self.shipstation_package_id.shipper_package_code or 'package',
                "confirmation": self.confirmation,
                "shipDate": ship_date,
                "weight": {
                    "value": total_weight,
                    "units": self.shipstation_instance_id.shipstation_weight_uom
                },
                "shipFrom": {
                    "name": warehouse.display_name or '',  # Warehouse name
                    "company": warehouse.company_id.display_name,  # warehouse company name
                    "street1": ship_from_partner.street or '',
                    "street2": ship_from_partner.street2 or '',
                    "city": ship_from_partner.city or '',
                    "state": ship_from_partner.state_id.code or '',
                    "postalCode": ship_from_partner.zip or '',
                    "country": ship_from_partner.country_id.code or '',
                    "phone": ship_from_partner.phone or '',
                },
                "shipTo": {
                    "name": ship_to_partner.name or '',
                    "company": ship_to_partner.company_name or (
                            ship_to_partner.parent_id and ship_to_partner.parent_id.name) or '',
                    "street1": ship_to_partner.street or '',
                    "street2": ship_to_partner.street2 or '',
                    "city": ship_to_partner.city or '',
                    "state": ship_to_partner.state_id.code or '',
                    "postalCode": ship_to_partner.zip or '',
                    "country": ship_to_partner.country_id.code or '',
                    "phone": ship_to_partner.phone or '',
                    "residential": self.is_residential,
                },
                "testLabel": not self.carrier_id.prod_environment
            }

            if carrier_id and carrier_id.shipping_provider_id:
                data.update({
                    "advancedOptions": {
                        "shippingProviderId": carrier_id.shipping_provider_id
                    }
                })

            self.prepare_dimensions_data(data, package, self.carrier_id.package_unit_default, carrier_id.default_package_id.shipper_package_code)

            if ship_to_partner.country_id and warehouse.partner_id.country_id and ship_to_partner.country_id.id != warehouse.partner_id.country_id.id:
                customs_items = []
                for move in self.move_ids:
                    customs_items_dict = {"customsItemId": move.id,
                                          "description": move.product_id.default_code,
                                          "quantity": int(move.product_uom_qty),
                                          "value": move.sale_line_id.price_unit if move.sale_line_id else 0}
                    if move.product_id.hs_code:
                        customs_items_dict.update({"harmonizedTariffCode": move.product_id.hs_code or ''})
                    if move.product_id.country_of_origin:
                        customs_items_dict.update({"countryOfOrigin": move.product_id.country_of_origin.code or ''})
                    customs_items.append(customs_items_dict)

                data.update({"internationalOptions": {
                    "contents": self.contents_of_international_shipment,
                    "customsItems": customs_items,
                    "nonDelivery": self.non_delivery_option
                }})

            response, code = instance.get_connection(url='/shipments/createlabel', data=data, method="POST")
            if code.status_code != 200:
                try:
                    res = json.loads(code.content.decode('utf-8')).get('ExceptionMessage')
                except:
                    res = code.content.decode('utf-8')
                msg = "107: Something went wrong while Getting label from " \
                      "ShipStation for Picking : {}.\n\n {}".format(self.name, res)
                _logger.exception(msg)
                if not self._context.get('from_delivery_order', True):
                    self.unlink_old_message_and_post_new_message(body=msg)
                    return
                else:
                    raise UserError(msg)

            binary_data = response.get('labelData', False)
            reference_code = response.get('trackingNumber')
            shipment_id = response.get('shipmentId')
            binary_data = binascii.a2b_base64(str(binary_data))
            message = ("Label created." + Markup("<br/>") + "Label Tracking Number : </b>%s" % reference_code)
            self.write({'is_get_shipping_label': True,
                        'carrier_tracking_ref': reference_code,
                        'shipstation_shipment_id': shipment_id})
            self.unlink_old_message_and_post_new_message(body=message, attachments=[
                ('Label-%s.%s' % (reference_code, "pdf"), binary_data)])
            shipping_cost = self.convert_company_currency_amount_to_order_currency(response.get('shipmentCost', 0))
            shipping_data = [{
                'exact_price': shipping_cost,
                'tracking_number': reference_code}]
            return shipping_data

    def get_shipstation_label_package_wise(self,carrier_id, instance, ship_date, warehouse, ship_from_partner,ship_to_partner):
        """
            ADD: This function is used for generate a label put in pack wise configuration.
            Task: 19728 - Generate the Shipping Label Package wise (Put-in-Pack) v17
            Add by: vaibhav chadaniya
            Args:
            carrier_id : shipstation carrier.
            instance : shipstation instance of current picking.
            ship_date : done date of picking
            warehouse : picking warehouse
            ship_from_partner : partner address from ship
            ship_to_partner : partner address where ship
        """
        shipping_data = []
        reference_code_list = []
        shipment_id_list = []
        for package in self.package_ids:
            total_weight = self.get_converted_weight_for_shipstation(
                package.shipping_weight)  # Use package weight if available
            msg = ''
            context = self._context.get('from_delivery_order', True)

            # Define field checks with error messages
            field_checks = [
                (total_weight, "Weight is not set"),
                (carrier_id.code, "Carrier code is not set"),
                (self.shipstation_service_id.service_code, "Service code is not set"),
                (self.shipstation_package_id.shipper_package_code, "Package code is not set"),
                (ship_from_partner.zip, "Postal Code in sender address is not set"),
                (ship_from_partner.country_id and ship_from_partner.country_id.code,
                 "Country code in sender address is not set"),
                (ship_to_partner.name, "Delivery partner name is not set"),
                (ship_to_partner.street, "Street in delivery partner address is not set"),
                (ship_to_partner.zip, "Postal code in delivery partner address is not set"),
                (ship_to_partner.country_id and ship_to_partner.country_id.code,
                 "Country code in delivery partner address is not set")
            ]

            # Check each field and accumulate error messages
            for field, error_message in field_checks:
                if not field:
                    msg += Markup("<br/>") + '- ' + error_message

            # Additional checks for international shipments
            if (self.partner_id.country_id and self.picking_type_id.warehouse_id.partner_id.country_id and
                    self.partner_id.country_id.id != self.picking_type_id.warehouse_id.partner_id.country_id.id):
                additional_checks = [
                    (self.contents_of_international_shipment, "Contents of International Shipment option is not set"),
                    (self.non_delivery_option, "Non-Delivery option is not set")
                ]
                for field, error_message in additional_checks:
                    if not field:
                        msg += '<br>' + '- ' + error_message

            # Return or raise an error based on context
            if msg:
                if context:
                    raise UserError("{} in Picking : {}".format(msg, self.name))
                return msg

            # Prepare package dimension and data
            package_dimension = False
            if not package_dimension and package.package_type_id.package_carrier_type == "shipstation_ept":
                package_dimension = package.package_type_id
            else:
                package_dimension = self.get_package_dimension()

            # Initialize package_code and assign as per condition
            package_code = False
            if package.package_type_id.package_carrier_type == "shipstation_ept":
                package_code = package.package_type_id.shipper_package_code
            elif self.shipstation_package_id:
                package_code = self.shipstation_package_id.shipper_package_code
            elif self.carrier_id:
                package_code = self.carrier_id.shipstation_package_id.shipper_package_code
            else:
                package_code = self.shipstation_carrier_id.default_package_id.shipper_package_code or 'package'

            if len(self.package_ids) == 1:
                package_code = package.package_type_id.shipper_package_code

            data = {
                "carrierCode": carrier_id.code,
                "serviceCode": self.shipstation_service_id.service_code,
                "packageCode": package_code,
                "confirmation": self.confirmation,
                "shipDate": ship_date,
                "weight": {
                    "value": total_weight,
                    "units": self.shipstation_instance_id.shipstation_weight_uom
                },
                "shipFrom": {
                    "name": warehouse.display_name or '',
                    "company": warehouse.company_id.display_name,
                    "street1": ship_from_partner.street or '',
                    "street2": ship_from_partner.street2 or '',
                    "city": ship_from_partner.city or '',
                    "state": ship_from_partner.state_id.code or '',
                    "postalCode": ship_from_partner.zip or '',
                    "country": ship_from_partner.country_id.code or '',
                    "phone": ship_from_partner.phone or '',
                },
                "shipTo": {
                    "name": ship_to_partner.name or '',
                    "company": ship_to_partner.company_name or (
                            ship_to_partner.parent_id and ship_to_partner.parent_id.name) or '',
                    "street1": ship_to_partner.street or '',
                    "street2": ship_to_partner.street2 or '',
                    "city": ship_to_partner.city or '',
                    "state": ship_to_partner.state_id.code or '',
                    "postalCode": ship_to_partner.zip or '',
                    "country": ship_to_partner.country_id.code or '',
                    "phone": ship_to_partner.phone or '',
                    "residential": self.is_residential,
                },
                "testLabel": not self.carrier_id.prod_environment
            }

            # Add advanced options for shipping provider if available
            if carrier_id and carrier_id.shipping_provider_id:
                data.update({
                    "advancedOptions": {
                        "shippingProviderId": carrier_id.shipping_provider_id
                    }
                })

            # Prepare dimensions for package-specific data
            self.prepare_dimensions_data(data, package_dimension, self.carrier_id.package_unit_default,
                                         carrier_id.default_package_id.shipper_package_code)

            # Add international options for customs items
            if ship_to_partner.country_id and warehouse.partner_id.country_id and ship_to_partner.country_id.id != warehouse.partner_id.country_id.id:
                customs_items = []
                for quant in package.quant_ids:
                    customs_items_dict = {
                        "customsItemId": quant.id,
                        "description": quant.product_id.default_code,
                        "quantity": int(quant.quantity),
                        "value": quant.product_id.list_price if quant.product_id else 0
                    }
                    if quant.product_id.hs_code:
                        customs_items_dict.update({"harmonizedTariffCode": quant.product_id.hs_code or ''})
                    if quant.product_id.country_of_origin:
                        customs_items_dict.update({"countryOfOrigin": quant.product_id.country_of_origin.code or ''})
                    customs_items.append(customs_items_dict)

                data.update({"internationalOptions": {
                    "contents": self.contents_of_international_shipment,
                    "customsItems": customs_items,
                    "nonDelivery": self.non_delivery_option
                }})

            # Create shipping label for the package
            response, code = instance.get_connection(url='/shipments/createlabel', data=data, method="POST")
            if code.status_code != 200:
                try:
                    res = json.loads(code.content.decode('utf-8')).get('ExceptionMessage')
                except:
                    res = code.content.decode('utf-8')
                msg = "107: Something went wrong while getting label from ShipStation for Picking : {}.\n\n {}".format(
                    self.name, res)

                _logger.exception(msg)
                if not self._context.get('from_delivery_order', True):
                    self.unlink_old_message_and_post_new_message(body=msg)
                    return
                else:
                    raise UserError(msg)
            binary_data = response.get('labelData', False)
            reference_code = response.get('trackingNumber')
            shipment_id = response.get('shipmentId')
            binary_data = binascii.a2b_base64(str(binary_data))
            message = ("Label created." + Markup("<br/>") + "Label Tracking Number : </b>%s" % reference_code)
            message = Markup(message)
            self.unlink_old_message_and_post_new_message(body=message, attachments=[
                ('Label-%s-%s.%s' % (reference_code,package_code, "pdf"), binary_data)])
            reference_code_list.append(reference_code)
            shipment_id_list.append(str(shipment_id))
            shipping_cost = self.convert_company_currency_amount_to_order_currency(response.get('shipmentCost', 0))
            shipping_data.append({
                'exact_price': shipping_cost,
                'tracking_number': reference_code
            })
        reference_code_string = ','.join(reference_code_list)
        shipment_id_string = ','.join(shipment_id_list)
        self.write({'is_get_shipping_label': True,
                    'carrier_tracking_ref': reference_code_string,
                    'shipstation_shipment_id': shipment_id_string})
        return shipping_data

    def delete_shipstation_label(self):
        """
            Modification: delete a multiple shipstation lable in put in pack case.
            Task: 19728 - Generate the Shipping Label Package wise (Put-in-Pack) v17
            Modified by: vaibhav chadaniya
        """
        attachments = self.env['ir.attachment']
        for picking in self:
            tracking_refs = picking.carrier_tracking_ref.split(',')
            for tracking_ref in tracking_refs:
                tracking_ref = tracking_ref.strip()
                if not tracking_ref:
                    continue
                label_name = ('Label-%s.%s' % (tracking_ref, "pdf"))
                attachments_ids = attachments.search(
                    [('res_model', '=', 'stock.picking'), ('res_id', 'in', [picking.id]), ('name', 'ilike', label_name)],
                    order='id desc')
                attachments_ids.sudo().unlink()

    def shipstation_ept_cancel_order(self):
        if not self.shipstation_order_id:
            raise UserError("Order is not having shipstation order number.")
        shipstation_store_id = self.shipstation_store_id
        if shipstation_store_id:
            if not self.weight:
                raise UserError("Weight of Picking not found..!")
            instance = shipstation_store_id.shipstation_instance_id
            data = self.prepare_order_export_data(is_cancel_order=True)
            data.update({"orderStatus": "cancelled"})
            response, code = instance.get_connection(url='/orders/createorder', data=data, method="POST")
            if code.status_code != 200:
                try:
                    res = json.loads(code.content.decode('utf-8')).get('ExceptionMessage')
                except:
                    res = code.content.decode('utf-8')
                msg = "108: Something went wrong while Cancelling order on ShipStation.\n\n %s" % res

                self.unlink_old_message_and_post_new_message(body=msg)
                _logger.exception(msg)
                return False
            if response.get('orderStatus') == "shipped":
                msg = "Order Cannot be Cancelled because it is 'Shipped' by ShipStation."
                self.unlink_old_message_and_post_new_message(body=msg)
                _logger.exception(msg)
                return False

            self.unlink_old_message_and_post_new_message(body="Order cancelled on ShipStation")
            self.write({
                'canceled_on_shipstation': True
            })
        return True

    def cancel_shipment_action(self):
        pickings = self.filtered(
            lambda x: x.shipstation_instance_id and x.carrier_tracking_ref and x.shipstation_shipment_id)
        for carrier in pickings.mapped('carrier_id'):
            carrier.shipstation_ept_cancel_shipment(pickings.filtered(lambda x: x.carrier_id == carrier))

    # def is_picking_contains_service_and_package(self):
    #     if not self.shipstation_service_id or not self.shipstation_package_id:
    #         msg = "Need to select shipstation service and package in Delivery Order to " \
    #               "Export order to shipstation."
    #         self.unlink_old_message_and_post_new_message(body=msg)
    #         raise UserError(msg)
    #     return True

    def is_picking_contains_store(self):
        if not self.shipstation_store_id:
            msg = "Need to select shipstation Store in Picking for export order to shipstation."
            self.unlink_old_message_and_post_new_message(body=msg)
            raise UserError(msg)
        return True

    def prepare_order_export_data(self, is_cancel_order=False):
        order_id = self.sale_id

        # Get the dates
        scheduled_date = self.scheduled_date.strftime("%Y-%m-%dT%H:%M:%S.0000000")
        order_date = order_id.date_order.strftime("%Y-%m-%dT%H:%M:%S.0000000") if order_id else scheduled_date

        shipstation_warehouse = self.env['shipstation.warehouse.ept'].search(
            ['|', ('odoo_warehouse_id', '=', self.picking_type_id.warehouse_id.id),
             ('is_default', '=', True), ('shipstation_instance_id', '=', self.shipstation_instance_id.id)], limit=1)
        if not shipstation_warehouse:
            raise UserError('No ShipStation Warehouse Mapping available in Odoo.')

        # Get total weight
        try:
            total_weight = self.get_converted_weight_for_shipstation()
        except Exception as e:
            raise UserError(e)

        # Get Carrier Code and Service Code
        carrier_id = False
        if self.carrier_id.get_cheapest_rates and self.shipstation_service_id:
            carrier_id = self.shipstation_service_id.shipstation_carrier_id
            carrier_code = carrier_id.code or ''
            service_code = self.shipstation_service_id.service_code or ''
        elif not self.carrier_id.get_cheapest_rates and self.carrier_id.delivery_type == 'shipstation_ept':
            carrier_id = self.carrier_id.shipstation_carrier_id
            carrier_code = carrier_id.code or ''
            service_code = self.carrier_id.shipstation_service_id.service_code or ''
        else:
            carrier_code = ''
            service_code = ''

        partner_shipping_id = order_id.partner_shipping_id if order_id else self.partner_id
        partner_invoice_id = order_id.partner_invoice_id if order_id else self.partner_id
        name = self.prepare_export_order_name(is_cancel_order)
        customer_email = self.get_email_address()

        context = self._context.get('from_delivery_order', True)
        msg = ''
        if not name:
            data_string = 'Order Number not set.'
            if not context:
                msg += Markup("<br/>") + '- ' + data_string
            else:
                raise UserError(data_string)
        if not order_date:
            data_string = 'Order Date not set.'
            if not context:
                msg += Markup("<br/>") + '- ' + data_string
            else:
                raise UserError(data_string)
        if not partner_invoice_id.name:
            data_string = 'Name of Invoice partner is not set.'
            if not context:
                msg += Markup("<br/>") + '- ' + data_string
            else:
                raise UserError(data_string)
        if not partner_shipping_id.name:
            data_string = 'Name of shipping partner is not set.'
            if not context:
                msg += Markup("<br/>") + '- ' + data_string
            else:
                raise UserError(data_string)
        if not partner_shipping_id.street:
            data_string = 'Street value in address of shipping partner is not set.'
            if not context:
                msg += Markup("<br/>") + '- ' + data_string
            else:
                raise UserError(data_string)
        if not partner_shipping_id.zip:
            data_string = 'ZipCode value in address of shipping partner is not set.'
            if not context:
                msg += Markup("<br/>") + '- ' + data_string
            else:
                raise UserError(data_string)

        if msg:
            return msg

        package = self.get_package_dimension()

        if len(self.package_ids) == 1:
            package_code = self.package_ids.package_type_id.shipper_package_code
        else:
            package_code = self.shipstation_package_id.shipper_package_code

        data = {
            "orderNumber": name,
            "orderKey": name,
            "orderDate": order_date,
            "shipByDate": scheduled_date,
            "customerUsername": self.partner_id.name,
            "customerEmail": customer_email,
            "shippingAmount": self.shipping_rates,
            "packageCode": package_code or '',
            "carrierCode": carrier_code,
            "serviceCode": service_code,
            "customerNotes": order_id.note if order_id and order_id.note else self.note if self.note else '',
            "weight": {
                "value": total_weight,
                "units": self.shipstation_instance_id.shipstation_weight_uom
            },
            "billTo": {
                "name": partner_invoice_id.name or '',
                "company": partner_invoice_id.company_id.name or '',
                "street1": partner_invoice_id.street or '',
                "street2": partner_invoice_id.street2 or '',
                "city": partner_invoice_id.city or '',
                "state": partner_invoice_id.state_id.code or '',
                "postalCode": partner_invoice_id.zip or '',
                "country": partner_invoice_id.country_id.code or '',
                "phone": partner_invoice_id.phone or '',
            },
            "shipTo": {
                "name": partner_shipping_id.name or '',
                "company": partner_shipping_id.company_name or partner_shipping_id.parent_id.name or '',
                "street1": partner_shipping_id.street or '',
                "street2": partner_shipping_id.street2 or '',
                "city": partner_shipping_id.city or '',
                "state": partner_shipping_id.state_id.code or '',
                "postalCode": partner_shipping_id.zip or '',
                "country": partner_shipping_id.country_id.code or '',
                "phone": partner_shipping_id.phone or '',
                "residential": self.is_residential,
            },
            "advancedOptions": {
                "warehouseId": shipstation_warehouse.shipstation_identification,
                "storeId": self.shipstation_store_id.shipstation_identification,
                "customField1": order_id and order_id.name or self.origin or '',
                "customField2": order_id and order_id.client_order_ref or ''
            }
        }

        if carrier_id and carrier_id.shipping_provider_id:
            data.get("advancedOptions").update({
                "shippingProviderId": carrier_id.shipping_provider_id
            })

        self.prepare_dimensions_data(data, package, self.carrier_id.package_unit_default, False)

        return data

    def _action_done(self):
        """
        Done pickings and make visible download button and send to shipper button based on
        condition.
        @return: return  response for done process
       """
        if len(self) > 1:
            res = super(StockPicking, self.with_context(from_delivery_order=False))._action_done()
        else:
            res = super(StockPicking, self)._action_done()

        for picking in self:
            if picking.carrier_tracking_ref and picking.batch_id and picking.shipstation_instance_id:
                picking.shipstation_send_to_shipper_process_done = True

        pickings_ready_for_download = self.filtered(lambda x: x.shipstation_send_to_shipper_process_done)
        if pickings_ready_for_download:
            pickings_ready_for_download.mapped('batch_id').shipstation_ready_for_download = True
        return res

    def is_order_shipped(self):
        url = '/orders/%s' % self.shipstation_order_id
        response, code = self.shipstation_instance_id.get_connection(url=url, data=None, params=None, method="GET")
        if code.status_code != 200:
            _logger.error("error when fetching the shipping status.")
            return False
        return response.get('orderStatus', '') == 'shipped'

    def get_exported_pickings(self):
        return self.sale_id.picking_ids.filtered(
            lambda pick: pick.shipstation_order_id and pick.id != self.id and pick.state != 'cancel')

    def prepare_line_export_data(self, line, move_id, process_lines):
        total_dict = {}
        product_data_list = []
        amount, tax = 0, 0
        if self.sale_id:
            qty = move_id.quantity if move_id.product_id == line.product_id else line.product_uom_qty
        else:
            qty = move_id.quantity

        if line and line.id not in process_lines and qty > 0 and self.sale_id:
            ship_product_id = self.find_ship_station_product_id(line.product_id, self.shipstation_instance_id)
            amount, tax = self.compute_tax_for_move_lines(line, qty)
            try:
                product_weight = self.get_converted_weight_for_shipstation(line.product_id.weight)
            except Exception as e:
                raise UserError(e)

            context = self._context.get('from_delivery_order', True)
            if not line.product_id.name:
                data_string = 'Name of product is not set.'
                if not context:
                    return Markup("<br/>") + '- ' + data_string, {}
                else:
                    raise UserError(data_string)

            line_dict = {
                "lineItemKey": line.product_id.id,
                "sku": line.product_id.default_code or '',
                "upc": line.product_id.barcode or '',
                "name": line.product_id.name or '',
                "weight": {
                    "value": product_weight,
                    "units": self.shipstation_instance_id.shipstation_weight_uom
                },
                "quantity": int(qty),
                "unitPrice": self.convert_amount_to_company_currency(
                    line.currency_id.round((line.price_subtotal / line.product_uom_qty))),
                "taxAmount": tax
            }
            if ship_product_id:
                line_dict.update({"productId": ship_product_id.shipstation_identification})
            product_data_list.append(line_dict)
        else:
            ship_product_id = self.find_ship_station_product_id(move_id.product_id, self.shipstation_instance_id)
            unit_price = self.convert_amount_to_company_currency(
                move_id.product_id.currency_id.round(move_id.product_id.lst_price))
            amount = unit_price * qty
            try:
                product_weight = self.get_converted_weight_for_shipstation(move_id.product_id.weight)
            except Exception as e:
                raise UserError(e)
            line_dict = {
                "lineItemKey": move_id.product_id.id,
                "sku": move_id.product_id.default_code or '',
                "upc": move_id.product_id.barcode or '',
                "name": move_id.product_id.name or '',
                "weight": {
                    "value": product_weight,
                    "units": self.shipstation_instance_id.shipstation_weight_uom
                },
                "quantity": int(qty),
                "unitPrice": unit_price
            }
            if ship_product_id:
                line_dict.update({"productId": ship_product_id.shipstation_identification})
            product_data_list.append(line_dict)

        if move_id and line and line.product_id != move_id.product_id:
            kit_data = self.prepare_line_export_data_for_kit_products(move_id)
            if not kit_data:
                return False, total_dict
            if product_data_list:
                if product_data_list[0]['lineItemKey'] == kit_data['lineItemKey']:
                    product_data_list.pop()
            product_data_list.append(kit_data)
        total_dict.update({'total': amount, 'tax': tax})
        return product_data_list, total_dict

    def prepare_line_export_data_for_kit_products(self, move_id):
        ship_product_id = self.find_ship_station_product_id(move_id.product_id,
                                                            self.shipstation_instance_id)
        try:
            product_weight = self.get_converted_weight_for_shipstation(move_id.product_id.weight)
        except Exception as e:
            raise UserError(e)
        product_dict = {
            "lineItemKey": move_id.product_id.id,
            "sku": move_id.product_id.default_code or '',
            "upc": move_id.product_id.barcode or '',
            "name": move_id.product_id.name or '',
            "weight": {
                "value": product_weight
            },
            "quantity": int(move_id.quantity),
            "unitPrice": 0.0,
            "taxAmount": 0.0
        }
        if ship_product_id:
            product_dict.update({"productId": ship_product_id.shipstation_identification})
        return product_dict

    def find_ship_station_product_id(self, product_id, shipstation_instance_id):
        ship_product_id = self.env['shipstation.product.ept'].search(
            [('product_id', '=', product_id.id),
             ('shipstation_instance_id', '=', shipstation_instance_id.id)], limit=1)
        return ship_product_id

    def get_converted_weight_for_shipstation(self, weight=0):
        return self.carrier_id.convert_weight_for_shipstation(self.company_id.get_weight_uom_id(),
                                                              self.shipstation_instance_id.weight_uom_id,
                                                              weight or self.weight)

    def compute_tax_for_move_lines(self, line, qty):
        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
        taxes = line.tax_id.compute_all(price, line.order_id.currency_id, qty, product=line.product_id,
                                        partner=line.order_id.partner_shipping_id)
        tax = self.convert_amount_to_company_currency(sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])))
        amount = self.convert_amount_to_company_currency(
            line.currency_id.round((line.price_subtotal / line.product_uom_qty) * qty))
        return amount, tax

    def prepare_export_order_name(self, is_cancel_order=False):
        is_multi_step = True if self.picking_type_id.warehouse_id.delivery_steps in (
            'pick_ship', 'pick_pack_ship') else False
        is_internal_name = self.env['ir.config_parameter'].sudo().get_param('shipstation.internal_picking_name')
        if is_multi_step and is_internal_name == 'True':
            if not is_cancel_order:
                int_pick = self.get_internal_pickings() if not self.shipstation_order_id else self.get_exported_internal_pickings()
            else:
                int_pick = self.get_exported_internal_pickings()
            # We are not passing sale order reference in case of multistep delivery,
            # And keep sale order reference in single step delivery
            # because current customers not face any name related changes
            name = '{}'.format(int_pick and int_pick[0].name or '')
        else:
            if self.sale_id:
                name = '{}-{}'.format(self.sale_id.name, self.name)
            else:
                name = '{}'.format(self.name)
        return name

    def get_internal_pickings(self):
        return self.sale_id.picking_ids.filtered(
            lambda pick: pick.picking_type_id.code == 'internal'
                         and not pick.related_outgoing_picking
                         and pick.location_dest_id.id == self.location_id.id
                         and pick.state == 'done').sorted(key=lambda r: r.id)

    def get_exported_internal_pickings(self):
        return self.sale_id.picking_ids.filtered(lambda pick: pick.picking_type_id.code == 'internal'
                                                              and pick.state == 'done'
                                                              and pick.related_outgoing_picking.id == self.id).sorted(
            key=lambda r: r.id)

    def raise_warning_if_shipstation_carrier_not_found(self):
        if not self.carrier_id:
            raise UserError("Carrier is missing!!!")
        if self.carrier_id.delivery_type != 'shipstation_ept':
            raise UserError("No shipstation carrier found into picking {}".format(self.name))

    def unlink_old_message_and_post_new_message(self, body, attachments=[]):
        message_ids = self.env["mail.message"].sudo().search(
            [('model', '=', 'stock.picking'), ('res_id', '=', self.id), ('body', '=ilike', body)])
        message_ids.unlink()
        self.message_post(body=body, attachments=attachments)

    def find_outgoing_pickings_of_sale_order_and_export_to_shipstation(self):
        pending_outgoing_pickings = self.sale_id.picking_ids.filtered(
            lambda pick: pick.state != "done"
                         and pick.is_exported_to_shipstation == False
                         and pick.picking_type_id.code == "outgoing"
                         and not pick.shipstation_order_id and pick.shipstation_instance_id)
        if pending_outgoing_pickings:
            for picking in pending_outgoing_pickings:
                if picking.state in ('waiting', 'assigned'):
                    picking.action_assign()
                    if picking.state == 'assigned':
                        picking.with_context(from_delivery_order=False).export_order_to_shipstation()

    def action_cancel(self):
        for picking in self:
            if picking.shipstation_instance_id:
                result = False
                if not picking.is_exported_to_shipstation or not picking.shipstation_order_id:
                    _logger.info("Cannot cancel on ShipStation : {}, "
                                 "as it is pending to be exported to ShipStation".format(picking.id))
                    continue
                if not picking.shipstation_store_id:
                    _logger.info("Cannot cancel on ShipStation : {}, "
                                 "as ShipStation store not available in picking".format(picking.id))
                    continue
                if not picking.weight:
                    _logger.info("Cannot cancel on ShipStation : {}, "
                                 "as Weight of Picking not found".format(picking.id))
                    continue
                try:
                    result = picking.shipstation_ept_cancel_order()
                except Exception as e:
                    _logger.info("Error {} comes at the time of cancel order on ShipStation {}".format(e, picking.name))
                    self -= picking
                    continue
                if not result:
                    self -= picking
        res = super(StockPicking, self).action_cancel()
        return res

    def convert_amount_to_company_currency(self, amount):
        """
        Convert amount to company currency
        """
        if self.sale_id and amount:
            rate = self.env['res.currency']._get_conversion_rate(self.sale_id.currency_id, self.company_id.currency_id,
                                                                 self.company_id, datetime.now())
            return self.company_id.currency_id.round(amount * rate)
        return amount

    def convert_company_currency_amount_to_order_currency(self, amount):
        """
        Convert amount from USD currency to order or company currency
        """
        if amount:
            from_currency = self.carrier_id.shipstation_carrier_id.carrier_rate_currency_id \
                            or self.company_id.currency_id
            to_currency = self.sale_id.currency_id or self.company_id.currency_id
            rate = self.env['res.currency']._get_conversion_rate(from_currency, to_currency,
                                                                 self.company_id, datetime.now())
            if self.sale_id:
                return self.sale_id.currency_id.round(amount * rate)
            else:
                return self.company_id.currency_id.round(amount * rate)
        return amount

    def set_carrier_based_on_response(self, response):
        """
        Update the Carrier, Shipstation service and Package based on shipstation shipment response
        """
        if len(response.get('shipments')):
            vals = {}
            rec = response.get('shipments')[0]
            instance = self.shipstation_instance_id
            carrier = self.env['delivery.carrier']

            shipstation_carrier = self.env["shipstation.carrier.ept"]
            if rec.get('carrierCode', ''):
                shipstation_carrier = shipstation_carrier.search(
                    [('shipstation_instance_id', '=', instance.id), ('code', '=', rec.get('carrierCode', ''))], limit=1)
                if not shipstation_carrier:
                    shipstation_carrier = self.create_shipstation_carriers(rec)
                if (not self.shipstation_carrier_id) or (
                        self.shipstation_carrier_id and self.shipstation_carrier_id.code != rec.get('carrierCode', '')):
                    shipstation_carrier and vals.update({'shipstation_carrier_id': shipstation_carrier.id})

            shipstation_service = self.env["shipstation.services.ept"]
            if rec.get('serviceCode', ''):
                shipstation_service = shipstation_service.search(
                    [('service_code', '=', rec.get('serviceCode')),
                     ('shipstation_carrier_id', '=', shipstation_carrier.id)], limit=1)
                if not shipstation_service:
                    shipstation_service = self.create_shipstation_service(rec, shipstation_carrier.id)
                if (not self.shipstation_service_id) or (
                        self.shipstation_service_id and self.shipstation_service_id.service_code != rec.get(
                    'serviceCode', '')):
                    shipstation_service and vals.update({'shipstation_service_id': shipstation_service.id})

            shipstation_package = self.env['stock.package.type']
            if rec.get('packageCode', ''):
                shipstation_package = shipstation_package.search(
                    [('package_carrier_type', '=', instance.provider),
                     ('shipstation_carrier_id', '=', shipstation_carrier.id),
                     ('shipper_package_code', '=', rec.get('packageCode'))], limit=1)
                if not shipstation_package:
                    shipstation_package = self.create_shipstation_package(rec, shipstation_carrier.id)
                if (not self.shipstation_package_id) or (
                        self.shipstation_package_id and self.shipstation_package_id.shipper_package_code != rec.get(
                    'packageCode')):
                    shipstation_package and vals.update({'shipstation_package_id': shipstation_package.id})

            if shipstation_carrier:
                carrier = carrier.search(
                    [('shipstation_carrier_id', '=', shipstation_carrier.id),
                     ('delivery_type', '=', 'shipstation_ept'),
                     ('shipstation_instance_id', '=', instance.id),
                     ('shipstation_service_id', '=', shipstation_service.id)], limit=1)
                if not carrier:
                    carrier = self.create_shipping_method(rec, shipstation_carrier, shipstation_service,
                                                          shipstation_package)
                if (not self.carrier_id) or (self.carrier_id.id != carrier.id):
                    carrier and vals.update({'carrier_id': carrier.id})
            vals and self.write(vals)
        return True

    def create_shipstation_carriers(self, response):
        """
        If Shipstation carrier not available then create it based on the shipment response
        """
        shipstation_carrier = self.env['shipstation.carrier.ept'].create({
            'name': response.get('carrierCode', False),
            'code': response.get('carrierCode', False),
            'shipstation_instance_id': self.shipstation_instance_id.id,
            'company_id': self.company_id.id
        })
        _logger.info("Instance:{}, Shipstation Carrier Code:{}".format(
            self.shipstation_instance_id.id, shipstation_carrier.code))
        return shipstation_carrier

    def create_shipstation_service(self, response, shipstation_carrier_id):
        """
        If Shipstation service not available then create it based on the shipment response
        """
        shipstation_service = self.env['shipstation.services.ept'].create({
            'service_name': response.get('serviceCode', False),
            'service_code': response.get('serviceCode', False),
            'service_type': 'both',
            'shipstation_carrier_id': shipstation_carrier_id,
            'shipstation_instance_id': self.shipstation_instance_id.id,
            'company_id': self.company_id.id
        })
        _logger.info("Instance:{}, Shipstation Service Code:{}".format(
            self.shipstation_instance_id.id, shipstation_service.service_code))
        return shipstation_service

    def create_shipstation_package(self, response, shipstation_carrier_id):
        """
        If Shipstation package not available then create it based on the shipment response
        """
        shipstation_package = self.env['stock.package.type'].create({
            'name': response.get('packageCode', False),
            'shipper_package_code': response.get('packageCode', False),
            'shipstation_carrier_id': shipstation_carrier_id,
            'shipstation_instance_id': self.shipstation_instance_id.id,
            'package_carrier_type': self.shipstation_instance_id.provider,
            'company_id': self.company_id.id
        })
        _logger.info("Instance:{}, Shipstation Package Code:{}".format(
            self.shipstation_instance_id.id, shipstation_package.shipper_package_code))
        return shipstation_package

    def create_shipping_method(self, response, shipstation_carrier, shipstation_service, shipstation_package):
        product_id = self.env['product.product'].search([('default_code', '=', 'SHIP_SHIPSTATION'),
                                                         ('company_id', '=', self.company_id.id)])
        vals = {
            "name": response.get('serviceCode', False),
            "delivery_type": "shipstation_ept",
            "shipstation_carrier_code": shipstation_carrier.code + '-' + shipstation_service.service_code,
            "shipstation_instance_id": self.shipstation_instance_id.id,
            "product_id": product_id.id,
            'shipstation_package_id': shipstation_package.id,
            'shipstation_carrier_id': shipstation_carrier.id,
            'integration_level': 'rate',
            'shipstation_service_id': shipstation_service.id,
            'prod_environment': self.shipstation_instance_id.prod_environment,
            "company_id": self.company_id.id
        }
        carrier = self.env['delivery.carrier'].create(vals)
        _logger.info(
            "Instance: {}, Shipstation Carrier: {}, Shipstation Service: {}, "
            "Carrier: {}".format(vals.get('shipstation_instance_id'), vals.get('shipstation_carrier_id'),
                                 vals.get('shipstation_service_id'), vals.get('shipstation_carrier_code')))
        return carrier

    def is_order_pick_ship(self):
        return True if self.picking_type_id.warehouse_id.delivery_steps in ('pick_ship', 'pick_pack_ship') else False

    def find_outgoing_picking(self):
        return (self.sale_id.picking_ids.filtered(
            lambda pick: pick.state == "assigned" and pick.picking_type_id.code == "outgoing" and pick.export_order)
                .mapped('move_ids').filtered(lambda line: line.quantity).mapped('picking_id'))

    def check_is_order_shipped_and_create_back_order(self):
        order_shipped = self.is_order_shipped()
        if order_shipped:
            ship_order_ref = self.shipstation_order_id
            _logger.info(
                "Picking {}:{}, Order Id: {} already shipped".format(self.id, self.name, ship_order_ref))
            for move in self.move_ids:
                move.write({'quantity': move.shipstation_exported_qty})
            wiz = self.button_validate()
            if wiz and isinstance(wiz, dict):
                try:
                    wiz = Form(self.env['stock.backorder.confirmation'].with_context(wiz['context'])).save()
                    wiz.with_context(button_validate_picking_ids=[self.id]).process()
                except Exception as e:
                    _logger.info("Error {} comes at the time of validating picking {}".format(e, self.name))
                    return False
            if wiz and not self.state == 'done':
                return False
        return True

    def find_related_outgoing_picking_and_export(self):
        outgoing_pickings = self.find_outgoing_picking()
        if outgoing_pickings:
            _logger.info("Start Process for Internal Picking: {}, Sale Order: {}".format(self.id, self.sale_id.name))
        for picking in outgoing_pickings:
            _logger.info("Pickings {}:{}, Shipstation Order Id: {}".format(picking.id, picking.name,
                                                                           picking.shipstation_order_id))
            picking.export_order_to_shipstation()
        return True

    def get_email_address(self):
        """
        Use : Get the customer email address in below flow for export order to ShipStation
                1. Email address of the shipping address.
                2. Email address of the parent partner of the shipping partner
                3. Email address of the sales order’s customer
                4. Email address of the billing address
        """
        if self.partner_id.email:
            return self.partner_id.email
        else:
            if self.partner_id.parent_id and self.partner_id.parent_id.email:
                return self.partner_id.parent_id.email
            else:
                if self.sale_id:
                    if self.sale_id.partner_id.email:
                        return self.sale_id.partner_id.email
                    elif self.sale_id.partner_invoice_id.email:
                        return self.sale_id.partner_invoice_id.email
        return ''
