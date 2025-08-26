import json
import logging
import base64
from urllib.parse import quote
from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    """
    inheriting delivery carrier for shipstation implementation.
    """
    _inherit = 'delivery.carrier'
    _description = 'Delivery Carrier'

    shipstation_instance_id = fields.Many2one("shipstation.instance.ept",  ondelete='restrict')
    shipstation_carrier_id = fields.Many2one('shipstation.carrier.ept',
                                             string="Shipstation Carrier")
    # shipstation_weight_uom = fields.Selection([('grams', 'Grams'),
    #                                            ('pounds', 'Pounds'),
    #                                            ('ounces', 'Ounces')], default='grams',
    #                                           string="Supported Weight UoM",
    #                                           help="Supported Weight UoM by ShipStation")
    delivery_type = fields.Selection(selection_add=[("shipstation_ept", "Shipstation")],
                                     ondelete={'shipstation_ept': 'cascade'})
    package_unit_default = fields.Selection([('inches', 'Inches'),
                                             ('centimeters', 'Centimeters')],
                                            string="Package Unit", default='inches')
    is_residential_address = fields.Boolean("Is for Residential Address", default=False)

    shipstation_service_id = fields.Many2one('shipstation.services.ept', string='Shipstation Service',
                                             help="Shipstation service to use for the order from this carrier.")
    confirmation = fields.Selection([('none', 'None'),
                                     ('delivery', 'Delivery'),
                                     ('signature', 'Signature'),
                                     ('adult_signature', 'Adult Signature'),
                                     ('direct_signature', 'Direct Signature')],
                                    default="none", copy=False,
                                    help="Shipstation order confirmation level for order using this carrier.")
    shipstation_package_id = fields.Many2one('stock.package.type',
                                             string='Shipstation Package',
                                             copy=False,
                                             help="Shipstation package to use for this carrier.")
    get_cheapest_rates = fields.Boolean("Cheapest Carrier Selection ?",
                                        help="True: User need to manually get rates and select the service and package "
                                             "in Delivery order when using this carrier.\n "
                                             "False: Service and package will be required and will automatically "
                                             "set in Delivery Order.", default=False)

    # shipstation_weight_uom_id = fields.Many2one('uom.uom',
    #                                             domain=lambda self: [('category_id.id', '=',
    #                                                                   self.env.ref('uom.product_uom_categ_kgm').id)],
    #                                             string='Shipstaion UoM',
    #                                             help="Set equivalent unit of"
    #                                                  " measurement according to "
    #                                                  "provider unit of measurement."
    #                                                  " For Example, if the provider unit of "
    #                                                  "measurement is KG then you have to select KG "
    #                                                  "unit of measurement in the Shipstation Unit of"
    #                                                  " Measurement field.")
    shipstation_carrier_code = fields.Char(string="Shipstation Requested Shipping Service Name")
    shipstation_carrier_ids = fields.Many2many('shipstation.carrier.ept',
                                             string="Shipstation Carriers")
    shipstation_service_ids = fields.Many2many('shipstation.services.ept', string='Shipstation Services',
                                            help="Shipstation service to use for the order from this carrier.")

    def shipstation_ept_send_shipping(self, pickings):
        """
        This method is created to fetch shipstaion labels for the pickings
        if Delivery Order is fulfilled from odoo.
        @param pickings: Contains the value of stock.picking
        """
        result = []
        picking_ids = pickings.filtered(lambda x: not x.export_order)
        for picking in picking_ids:
            if not self._context.get('from_delivery_order', True):
                result = picking.with_context(from_delivery_order=True).get_shipstation_label()
            else:
                result = picking.get_shipstation_label()
        if not result:
            result += [{'exact_price': 0.0, 'tracking_number': ''}]
        return result

    def shipstation_ept_rate_shipment(self, orders):
        """
        This method is to fetch rates from shipstation, when requesting from website or sale order.
        :param orders: record of sale.order
        :return: it will return the price for cheapest carrier service and set
        the service,store and instance in the sale.order
        """
        price = 0.0
        for order in orders:
            if (not self.shipstation_service_id or not self.shipstation_package_id) and self.get_cheapest_rates is False:
                msg = ("There are multiple rates available on the Shipstation "
                       "therefore rate will be available on the Delivery Order.")
                return {'success': False, 'price': float(price), 'error_message': msg, 'warning_message': False}
            shipstation_warehouse = self.env['shipstation.warehouse.ept'].search(
                ['|', ('odoo_warehouse_id', '=', order.warehouse_id.id),
                 ('is_default', '=', True),
                 ('shipstation_instance_id', '=', self.shipstation_instance_id.id)], limit=1)
            if shipstation_warehouse:
                shipstation_service_obj = self.env['shipstation.services.ept']
                shipstation_services = self.shipstation_service_id
                shipstation_carriers = shipstation_services.shipstation_carrier_id
                data = {"serviceCode": shipstation_services.service_code,
                        "packageCode": self.shipstation_package_id.shipper_package_code or 'package'}
                instance = self.shipstation_instance_id
                shipping_partner_id = order.partner_shipping_id
                total_weight = sum([(line.product_id.weight * line.product_uom_qty) for line in
                                    order.order_line]) or 0.0
                try:
                    total_weight = self.convert_weight_for_shipstation(
                        order.company_id and order.company_id.get_weight_uom_id(),
                        self.shipstation_instance_id.weight_uom_id, total_weight)
                except Exception as e:
                    return {'success': False, 'price': float(price),
                            'error_message': "Something went wrong while converting weight",
                            'warning_message': False}
                # check cheapest rate is enabled
                if self.get_cheapest_rates is True:
                    shipstation_carriers = self.shipstation_carrier_ids
                    data = {"packageCode": self.shipstation_package_id.shipper_package_code or 'package'}
                cheapest_carriers = []

                _logger.info("here 1=================")
                _logger.info(data)
                _logger.info("here 2=================")
                cheapest_carriers_vals = self.get_cheapest_carriers(cheapest_carriers, price, shipstation_carriers, data, shipstation_warehouse, shipping_partner_id, total_weight, instance, order, shipstation_service_obj)
                _logger.info(cheapest_carriers_vals)
                _logger.info("here 3=================")

                cheapest_carriers = cheapest_carriers_vals.get('cheapest_carriers', False)
                code = cheapest_carriers_vals.get('code')
                if cheapest_carriers:
                    finalised_carrier = sorted(cheapest_carriers, key=lambda x: x['price'])
                    price = finalised_carrier[0]['price']
                    service_id = self.env['shipstation.services.ept'].search([
                        ('service_code', '=', finalised_carrier[0]['servicecode']),
                        ('shipstation_carrier_id', '=', finalised_carrier[0]['carrier'].id)], limit=1)
                    carrier = finalised_carrier[0]['carrier']
                    order.cheapest_service_id = service_id
                    order.cheapest_carrier_id = carrier
                    price = self.convert_shipping_rate(price, carrier.carrier_rate_currency_id, order)
                    return {'success': True, 'price': float(price), 'error_message': False, 'warning_message': False}
                else:
                    msg = "115 : Something went wrong while Getting Rates from" \
                          "ShipStation.\n\n %s" % (code.content.decode('utf-8'))
                    _logger.exception(msg)
                    return {
                        'success': False,
                        'price': float(price),
                        'error_message': "No rates available",
                        'warning_message': False
                    }
            else:
                msg = "116 : Warehouse configuration not found while Getting Rates from ShipStation."
                order.unlink_old_message_and_post_new_message(body=msg)
                _logger.exception(msg)
                return {
                    'success': False,
                    'price': float(price),
                    'error_message': "No rates available",
                    'warning_message': False
                }

    def get_data(self, data, carrier, shipstation_warehouse, shipping_partner_id, total_weight):
        data.update({
            "carrierCode": carrier.code,
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
            "residential": self.is_residential_address,
        })

        """
        Pass (fromCity,fromState,fromWarehouseId) parameters in get rate API if available.
        """
        if shipstation_warehouse.origin_address_id.city:
            data.update({"fromCity": shipstation_warehouse.origin_address_id.city})
        if shipstation_warehouse.origin_address_id.state_id.code:
            data.update({"fromState": shipstation_warehouse.origin_address_id.state_id.code})
        if shipstation_warehouse.shipstation_identification:
            data.update({"fromWarehouseId": str(shipstation_warehouse.shipstation_identification)})

        _logger.info("here 1a=================")
        self.env['stock.picking'].prepare_dimensions_data(data, self.shipstation_package_id, self.package_unit_default, False)
        return data

    def get_cheapest_carriers(self, cheapest_carriers, price, shipstation_carriers, data, shipstation_warehouse, shipping_partner_id, total_weight, instance, order, shipstation_service_obj):
        code = False
        for carrier in shipstation_carriers:
            querystring = {'carrierCode': carrier.code}
            data = self.get_data(data, carrier, shipstation_warehouse, shipping_partner_id, total_weight)
            _logger.info("here 2a=================")
            _logger.info(data)
            _logger.info("here 2b=================")
            _logger.info(querystring)
            _logger.info("here 2c=================")
            
            response, code = instance.get_connection(url='/shipments/getrates', data=data, params=querystring,
                                                     method="POST")
            if not response or code.status_code != 200:
                if self.get_cheapest_rates is True:
                    continue
                else:
                    msg = "100 : Something went wrong while Getting Rates from" \
                          "ShipStation.\n\n %s" % (code.content.decode('utf-8'))
                    _logger.exception(msg)
                    return {
                        'success': False,
                        'price': float(price),
                        'error_message': "No rates available",
                        'warning_message': False,
                        'code': code
                    }

            # Filter the cheapest rate based on selected services
            selected_services = self.shipstation_service_ids.filtered(
                lambda x: x.shipstation_carrier_id.id == carrier.id).mapped('service_code')
            for result in response:
                # If response service not exist in selected service then Skip
                if self.get_cheapest_rates and selected_services:
                    if result.get('serviceCode', False) not in selected_services:
                        continue
                # If price not available then Skip
                price = result.get('shipmentCost', False)
                other_cost = result.get('otherCost', False)
                if other_cost:
                    price += other_cost
                service_id = shipstation_service_obj.search(
                    [('service_code', '=', result.get('serviceCode', False)),
                     ('shipstation_carrier_id', '=', carrier.id)], limit=1)
                # If price not available or service not available then Skip
                if not service_id or not price:
                    continue

                cheapest_carriers.append({
                    'price': price,
                    'servicecode': service_id.service_code,
                    'carrier': carrier
                })
        val = {
            'cheapest_carriers': cheapest_carriers,
            'code': code
        }
        return val

    def shipstation_ept_cancel_shipment(self, picking_ids):
        """This method is used to cancel the picking from the shipstation
        Modify By - Vaibhav Chadaniya
        19728 - Generate the Shipping Label Package wise (Put-in-Pack) v17
        change to support cancel multiple shipment with multiple shipment ID.
        @param picking_ids: This will contains the record of stock.picking
        @return"""
        for picking in picking_ids:
            if picking.shipstation_shipment_id:
                ship_id=str(picking.shipstation_shipment_id)
                shipment_ids = ship_id.split(',')
                for shipment_id in shipment_ids:
                    shipment_id = int(shipment_id.strip())
                    if not shipment_id:
                        continue
                    data = {"shipmentId": shipment_id}
                    instance = picking.shipstation_instance_id
                    response, code = instance.get_connection(url='/shipments/voidlabel', data=data, method="POST")
                    if code.status_code != 200:
                        try:
                            res = json.loads(code.content.decode('utf-8')).get('ExceptionMessage')
                        except:
                            res = code.content.decode('utf-8')
                        msg = "101 : Something went wrong while Canceling label on " \
                              "ShipStation.\n\n %s" % res
                        picking.unlink_old_message_and_post_new_message(body=msg)
                        _logger.exception(msg)
                        raise UserError(msg)
                    if response.get('approved'):
                        picking.unlink_old_message_and_post_new_message(body="Shipment Cancelled on ShipStation.")
                picking.write({'canceled_on_shipstation': True})
                picking.delete_shipstation_label()
        return True

    def shipstation_ept_get_tracking_link(self, picking):
        """This method is used to get the tracking link for shipstation order
        1. if shipstation instance Do you want to use Shipstation Tracking Link for all shipping provider?
        2. if yes than take shipment tracking url from instance
        3. If not then tracking url take from shipstation carrier and prepare from it.
        @param picking: contains the record of stock.picking
        @return: returns the url link"""
        url = ''
        tracking_url_from_instance = True
        if self.shipstation_instance_id.use_same_tracking_link_for_all_shipping_provider:
            if self.shipstation_instance_id.tracking_link:
                url = str(self.shipstation_instance_id.tracking_link)
        elif not self.shipstation_instance_id.use_same_tracking_link_for_all_shipping_provider:
            if self.shipstation_carrier_id.tracking_url:
                url = str(self.shipstation_carrier_id.tracking_url)
                tracking_url_from_instance = False
            elif self.shipstation_instance_id.tracking_link:
                url = str(self.shipstation_instance_id.tracking_link)
        if url:
            if tracking_url_from_instance:
                tracking_number = picking.carrier_tracking_ref
                carrier_code = picking.shipstation_carrier_id.code
                postal_code = quote(picking.partner_id.zip)
                locale = self._context.get('lang') or 'en'
                shipstation_order_number = picking.prepare_export_order_name() if not picking.exported_order_to_shipstation else picking.exported_order_to_shipstation
                order_number = base64.b64encode(shipstation_order_number.encode()).decode()
                tracking_url = '%s&carrier_code=%s&tracking_number=%s&order_number=%s&postal_code=%s&locale=%s' % (
                    url, carrier_code, tracking_number, order_number, postal_code, locale)
                return tracking_url
            else:
                if '{TRACKING_NUMBER}' in url:
                    tracking_url = url.replace('{TRACKING_NUMBER}', str(picking.carrier_tracking_ref))
                else:
                    tracking_url = '%s%s' % (url, str(picking.carrier_tracking_ref))
                return tracking_url
        return False

    def convert_weight_for_shipstation(self, from_uom_unit, to_uom_unit, weight):
        """This will convert the given weight from shipstation
        @param from_uom_unit: value of uom
        @param to_uom_unit: value of uom
        @param weight: Total weight"""
        return from_uom_unit._compute_quantity(weight, to_uom_unit)

    # @api.onchange('shipstation_weight_uom')
    # def onchange_shipstation_weight_uom(self):
    #     for rec in self:
    #         if rec.shipstation_weight_uom:
    #             mapping_rec = self.env["shipstation.weight.mapping"].search(
    #                 [('shipstation_weight_uom', '=', rec.shipstation_weight_uom)], limit=1)
    #         if not mapping_rec:
    #             raise UserError(
    #                 "No weight mapping found for {}, Please define first!!!".format(rec.shipstation_weight_uom))
    #         rec.shipstation_weight_uom_id = mapping_rec.shipstation_weight_uom_id.id

    def convert_shipping_rate(self, amount, from_currency, order):
        """
        Convert shipping rate from carrier currency to order or company currency
        @param amount: Amount to convert
        @param from_currency: Currency id
        @param order: record of sale.order
        @return: will returns the converted amount
        """
        if amount:
            if not from_currency:
                from_currency = order.company_id.currency_id
            rate = self.env['res.currency']._get_conversion_rate(from_currency, order.currency_id,
                                                                 order.company_id, datetime.now())
            return order.currency_id.round(amount * rate)
        return amount
