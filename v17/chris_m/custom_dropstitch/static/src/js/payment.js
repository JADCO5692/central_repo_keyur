/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.PartialPayment.include({
    init: function () {
        // const $paymentCheckbox = $('#payment_checkbox');
        // const $paymentValues = $('#payment_values');
        // const $paymentInvoiceCheckbox = $('#payment_invoice_checkbox');
        // const $paymentInvoiceValues = $('#payment_invoice_values');

        // $paymentCheckbox.prop('checked', false);
        // $paymentValues.hide();
        // $paymentInvoiceCheckbox.prop('checked', false);
        // $paymentInvoiceValues.hide();

        const amount = $('#order_total').length ? parseFloat($('#order_total').text()) :
                      $("#amount_total").length ? parseFloat($("#amount_total").val()) : 0;
        jsonrpc('/check_partial_payment_configuration', {
            data: { amount },
            success: function (res) {
                const hide = JSON.parse(res).hide;
                const displayStyle = hide ? 'none' : '';
                $('.switch, .payment_checkbox_label, .invoice_partial_payment_switch_button, .partial_payment_switch_button, .sale_order_partial_payment_switch_button').css('display', displayStyle);
            }
        });
    },
    start: function(){
        this._super.apply(this, arguments);
        let $partial_pay = $('#partial_payment_values'); 
        if($partial_pay.length){
            $partial_pay.find('#payment_values').trigger('change');
            $partial_pay.find('#payment_values').attr('disabled','')
        }
    },
});
     
