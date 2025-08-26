/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.websiteSaleDelivery.include({
    _handleCarrierUpdateResult: async function (carrierInput) {
        const result = await this.rpc('/shop/update_carrier', {
            'carrier_id': carrierInput.value,
            'no_reset_access_point_address': this.forceClickCarrier,
        })
        this.result = result;
        this._handleCarrierUpdateResultBadge(result);
        if (carrierInput.checked) {
            var amountDelivery = document.querySelector('#order_delivery .monetary_field');
            var amountUntaxed = document.querySelector('#order_total_untaxed .monetary_field');
            var amountTax = document.querySelector('#order_total_taxes .monetary_field');
            var amountTotal = document.querySelectorAll('#order_total .monetary_field, #amount_total_summary.monetary_field');

            amountDelivery.innerHTML = result.new_amount_delivery;
            amountUntaxed.innerHTML = result.new_amount_untaxed;
            amountTax.innerHTML = result.new_amount_tax;
            amountTotal.forEach(total => total.innerHTML = result.new_amount_total);
            // we need to check if it's the carrier that is selected
            let pay_val = $('#payment_values').val();
            if (pay_val){
                pay_val = parseFloat(pay_val);
            }
            if (pay_val && result.new_amount_total_raw !== undefined) {
                this._updateShippingCost(result.new_amount_total_raw);
                // reload page only when amount_total switches between zero and not zero
                const hasPaymentMethod = document.querySelector(
                    "div[name='o_website_sale_free_cart']"
                ) === null;
                const shouldDisplayPaymentMethod = result.new_amount_total_raw !== 0;
                if (hasPaymentMethod !==  shouldDisplayPaymentMethod) {
                    location.reload(false);
                }
            }
            this._updateShippingCost(result.new_amount_delivery);
        }
        this._enableButton(result.status);
        let currentId = result.carrier_id
        const showLocations = document.querySelectorAll(".o_show_pickup_locations");

        for (const showLoc of showLocations) {
            const currentCarrierId = showLoc.closest("li").getElementsByTagName("input")[0].value;
            if (currentCarrierId == currentId) {
                this._specificDropperDisplay(showLoc);
                break;
            }
        }
    },
});