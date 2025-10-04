/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import "@website_sale/js/checkout";   // load checkout widget
const WebsiteSaleCheckout = publicWidget.registry.WebsiteSaleCheckout;

WebsiteSaleCheckout.include({
    async _selectDeliveryMethod(ev) {
        // Call original behavior
        await this._super(...arguments);

        const checkedRadio = ev.currentTarget;
        if (!checkedRadio) {
            return;
        }

        // Check if carrier has `is_custom_cargo`
        const isCustomCargo = checkedRadio.dataset.isCustomCargo === "true";

        if (isCustomCargo) {
            // Show cargo fields
            document.querySelector("#air_cargo_fields")?.classList.remove("d-none");

            // Hide delivery address section
            document.querySelector("#delivery_address_row")?.classList.add("d-none");
        } else {
            // Hide cargo fields
            document.querySelector("#air_cargo_fields")?.classList.add("d-none");

            // Show delivery address section
            document.querySelector("#delivery_address_row")?.classList.remove("d-none");
        }
    },
});
