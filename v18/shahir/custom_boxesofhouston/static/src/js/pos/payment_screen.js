
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { RoutePickerPopup } from "@custom_boxesofhouston/js/pos/route_picker_popup/route_picker_popup" 
import { onWillStart, onMounted, useRef, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation"; 

patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this.get_pos_routes = {};
        onWillStart(async () => {
            this.get_pos_routes = await this.env.services.orm.call("pos.config", "get_pos_routes",[this.pos.config.id]);
        });
    },
    select_route(){
        let self = this;
        debugger
        if (this.get_pos_routes.length) {
            this.dialog.add(RoutePickerPopup, {
                current_route:self.currentOrder.route_id?String(self.currentOrder.route_id):'',
                routes:this.get_pos_routes,
                title: _t("Select Shipping Route"),
                getPayload: (shippingRoute) => {
                    self.currentOrder.setShippingRoute(shippingRoute);
                },
            });
        } else {
            self.currentOrder.route_id = false
        }
    }
});