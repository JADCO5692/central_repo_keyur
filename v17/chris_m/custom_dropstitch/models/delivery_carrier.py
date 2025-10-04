# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.addons.stock_delivery.models.delivery_request_objects import DeliveryCommodity, DeliveryPackage
from odoo.addons.delivery_ups_rest.models.ups_request import UPSRequest
from odoo.addons.delivery_fedex_rest.models.fedex_request import FedexRequest
from odoo.tools import pdf
from markupsafe import Markup

import base64
import logging

_logger = logging.getLogger(__name__)

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'
    
    hide_price_from_ecom = fields.Boolean('Hide price from ECommerce')
    custom_secondary_default_carrier = fields.Boolean('Secondary Default Carrier')
    custom_hide_for_sel = fields.Boolean('Hide from General Selection')
    custom_outside_usa = fields.Boolean('Outside USA')
    #def _is_available_for_order(self, order):
    #    if order.partner_id.property_delivery_carrier_id.id == self.id:
    #        return True
    #    else:
    #        if self.get_cheapest_rates and order._get_estimated_weight() <= 20:
    #            return True        
    #    return False 
    
    def fedex_rest_send_shipping_wave(self, waves):
        res = []
        srm = FedexRequest(self)
        for wave in waves:
            packages = self._get_packages_from_wave(wave, self.fedex_rest_default_package_type_id)
            response = srm._ship_package(
                ship_from_wh=wave.move_line_ids[0].picking_id.picking_type_id.warehouse_id.partner_id,
                ship_from_company=wave.move_line_ids[0].picking_id.company_id.partner_id,
                ship_to=wave.move_line_ids[0].picking_id.partner_id,
                sold_to=wave.move_line_ids[0].picking_id.sale_id.partner_invoice_id,
                packages=packages,
                currency=wave.move_line_ids[0].picking_id.sale_id.currency_id.name or wave.company_id.currency_id.name,
                order_no=wave.name,
                customer_ref=wave.move_line_ids[0].picking_id.sale_id.client_order_ref,
                picking_no=wave.name,
                incoterms=wave.move_line_ids[0].picking_id.sale_id.incoterm.code,
                freight_charge=wave.move_line_ids[0].picking_id.sale_id.order_line.filtered(lambda sol: sol.is_delivery and sol.product_id == self.product_id).price_total,
            )

            warnings = response.get('alert_message')
            if warnings:
                _logger.info(warnings)

            logmessage = (_("Shipment created into Fedex") + Markup("<br/>") +
                          response.get('service_info') + Markup("<br/><b>") +
                         _("Tracking Numbers:") + Markup("</b> ") + response.get('tracking_numbers') + Markup("<br/><b>") +
                         _("Packages:") + Markup("</b> ") + ','.join([p.name for p in packages if p.name]))

            if response.get('documents'):
                logmessage += Markup("<br/><b>") + _("Required documents:") + Markup("</b> ") + response.get('documents')

            attachments = [
                ('%s-%s.%s' % (self._get_delivery_label_prefix(), nr, self.fedex_rest_label_file_type), base64.b64decode(label))
                for nr, label in response.get('labels')
            ]
            if response.get('invoice'):
                attachments.append(('%s.pdf' % self._get_delivery_doc_prefix(), base64.b64decode(response.get('invoice'))))

            wave.message_post(body=logmessage, attachments=attachments)
            wave.custom_carrier_tracking_ref = response.get('tracking_numbers')
            for move_line in wave.move_line_ids[0]:
                move_line.picking_id.carrier_tracking_ref = response.get('tracking_numbers')

            res.append({'exact_price': response.get('price'), 'tracking_number': response.get('tracking_numbers')})

            if self.return_label_on_delivery:
                if len(packages) > 1:
                    wave.message_post(body=_("Automated return label generation is not supported by FedEx for multi-package shipments. Please generate the return labels manually."))
                else:
                    self.get_return_label(picking, tracking_number=response.get('tracking_numbers').split(',')[0], origin_date=response.get('date'))

        return res
    
    def _get_packages_from_wave(self, wave, default_package_type):
        packages = []

        # Create all packages.
        move_lines = wave.move_line_ids
        commodities = self._get_commodities_from_stock_move_lines(move_lines)
        package_total_cost = 0.0
        package = wave.move_line_ids[0].result_package_id
        for quant in package.quant_ids:
            package_total_cost += self._product_price_to_company_currency(
                quant.quantity, quant.product_id, wave.company_id
            )
            packages.append(DeliveryPackage(
                commodities,
                package.shipping_weight or package.weight,
                package.package_type_id,
                name=package.name,
                total_cost=package_total_cost,
                currency=wave.company_id.currency_id,
                picking=wave,
        ))

        return packages
    
    def ups_rest_send_shipping_wave(self, waves):
        res = []
        ups = UPSRequest(self)
        for wave in waves:
            packages, shipment_info, ups_service_type, ups_carrier_account, cod_info = self._prepare_shipping_data(wave.move_line_ids[0].picking_id)

            check_value = ups._check_required_value(picking=wave.move_line_ids[0].picking_id)
            if check_value:
                raise UserError(check_value)

            result = ups._send_shipping(
                shipment_info=shipment_info, packages=packages, carrier=self, shipper=wave.company_id.partner_id, ship_from=wave.move_line_ids[0].picking_id.picking_type_id.warehouse_id.partner_id,
                ship_to=wave.move_line_ids[0].picking_id.partner_id, service_type=ups_service_type, duty_payment=wave.custom_carrier_id.ups_duty_payment,
                saturday_delivery=wave.custom_carrier_id.ups_saturday_delivery, cod_info=cod_info,
                label_file_type=self.ups_label_file_type, ups_carrier_account=ups_carrier_account)

            company = wave.company_id or self.env.company
            currency_order = wave.move_line_ids[0].picking_id.sale_id.currency_id
            if not currency_order:
                currency_order = wave.company_id.currency_id

            if currency_order.name == result['currency_code']:
                price = float(result['price'])
            else:
                quote_currency = self.env['res.currency'].search([('name', '=', result['currency_code'])], limit=1)
                price = quote_currency._convert(
                    float(result['price']), currency_order, company, fields.Date.today())

            package_labels = result.get('label_binary_data', [])

            carrier_tracking_ref = "+".join([pl[0] for pl in package_labels])
            logmessage = _("Shipment created into UPS<br/>"
                           "<b>Tracking Numbers:</b> %s<br/>"
                           "<b>Packages:</b> %s") % (carrier_tracking_ref, ','.join([p.name for p in packages if p.name]))
            if self.ups_label_file_type != 'GIF':
                attachments = [('LabelUPS-%s.%s' % (pl[0], self.ups_label_file_type), pl[1]) for pl in package_labels]
            else:
                attachments = [('LabelUPS.pdf', pdf.merge_pdf([pl[1] for pl in package_labels]))]
            if result.get('invoice_binary_data'):
                attachments.append(('UPSCommercialInvoice.pdf', result['invoice_binary_data']))
            wave.message_post(body=logmessage, attachments=attachments)
            wave.custom_carrier_tracking_ref = carrier_tracking_ref
            for move_line in wave.move_line_ids[0]:
                move_line.picking_id.carrier_tracking_ref = carrier_tracking_ref
            shipping_data = {
                'exact_price': price,
                'tracking_number': carrier_tracking_ref}
            res = res + [shipping_data]
            if self.return_label_on_delivery:
                try:
                    self.ups_rest_get_return_label(picking)
                except (UserError, ValidationError) as err:
                    try:
                        ups._cancel_shipping(result['tracking_ref'])
                    except ValidationError:
                        pass
                    raise UserError(err)
        return res
    
    def convert_weight_for_shipstation(self, from_uom_unit, to_uom_unit, weight):
        weight = super().convert_weight_for_shipstation(from_uom_unit, to_uom_unit, weight)
        if self.shipstation_carrier_id.name != "Endicia":
            weight = weight + 1.5
        return weight