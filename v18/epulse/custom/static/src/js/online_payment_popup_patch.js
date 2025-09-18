/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { OnlinePaymentPopup } from "@pos_online_payment/app/online_payment_popup/online_payment_popup";

patch(OnlinePaymentPopup, {
    props : {
    qrCode: String,
        formattedAmount: String,
        orderName: String,
        close: Function,
        paymentUrl: String,
    },
    setup() {
        super.setup();
    },
});