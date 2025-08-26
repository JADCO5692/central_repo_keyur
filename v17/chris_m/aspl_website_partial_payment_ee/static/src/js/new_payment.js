/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.PartialNewPayment = publicWidget.Widget.extend({
    selector: '.o_portal_sidebar, #quote_content',

    init: function () {
        this.$paymentSaleOrderCheckbox = $('#payment_sale_order_checkbox');
        this.$paymentValuesVal = $("#payment_values_val");
        this.$paymentValuesVal.hide();
        this.$saleOrderId = $("#sale_order_id");
    },

    events: {
        'mousedown #payment_sale_order_checkbox': 'onMouseDownPaymentSoCheckbox',
        'change #payment_sale_order_checkbox': 'onChangePaymentSoCheckBox',
        'keyup #payment_values_val': 'onKeyUpPaymentValuesVal',
        'keypress #payment_values_val': 'onKeyPressPaymentValuesVal',
    },

    onMouseDownPaymentSoCheckbox: function (ev) {
        if (!this.$paymentSaleOrderCheckbox.is(':checked')) {
            this.$paymentSaleOrderCheckbox.trigger("change");
        }
    },

    onChangePaymentSoCheckBox: function (ev) {
        jsonrpc("/check_sale_order_partial_payment", {})
            .then(data => {
                const res1 = JSON.parse(data);
                if (res1 && res1.warning) {
                    this.$paymentSaleOrderCheckbox.prop('checked', false);
                    this.$paymentValuesVal.hide();
                    swal('You are not allowed to order more than ' + res1.max_partial_order + ' order, First please pay the Previous order. ', "error");
                }
            });

        const isChecked = this.$paymentSaleOrderCheckbox.is(':checked');
        this.$paymentValuesVal.toggle(isChecked);
        const amount = isChecked ? parseFloat(this.$paymentValuesVal.val()) : 0.0;
        this.updatePaymentAmount('/sale_order/partial_pay/price', amount);
    },

    onKeyUpPaymentValuesVal: function (ev) {
        const max = parseFloat(this.$paymentValuesVal.data('max'));
        let enteredAmount = parseFloat($(ev.currentTarget).val());
        if (enteredAmount > max) {
            swal('You cannot enter an amount greater than ' + max, "", "error");
            enteredAmount = max;
            $(ev.currentTarget).val(enteredAmount.toFixed(2));
        }
        this.updatePaymentAmount('/sale_order/partial_pay/price', enteredAmount);
    },

    onKeyPressPaymentValuesVal: function (e) {
        if (e.which != 8 && e.which != 0 && e.which != 46 && (e.which < 48 || e.which > 57)) {
            return false;
        }
    },

    updatePaymentAmount: function (endpoint, amount) {
        jsonrpc(endpoint, {
            amount,
            sale_order: this.$saleOrderId.val()
        });
    },
});
