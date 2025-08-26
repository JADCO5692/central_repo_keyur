/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.PartialPayment = publicWidget.Widget.extend({
    selector: '.oe_website_sale, #portal_pay',

    init: function () {
        const $paymentCheckbox = $('#payment_checkbox');
        const $paymentValues = $('#payment_values');
        const $paymentInvoiceCheckbox = $('#payment_invoice_checkbox');
        const $paymentInvoiceValues = $('#payment_invoice_values');

        $paymentCheckbox.prop('checked', false);
        $paymentValues.hide();
        $paymentInvoiceCheckbox.prop('checked', false);
        $paymentInvoiceValues.hide();

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

    events: {
        'change #payment_checkbox': 'onPaymentCheckboxChange',
        'change #payment_invoice_checkbox': 'onInvoiceCheckboxChange',
        'keyup #payment_values': 'onPaymentValuesChange',
        'change #payment_values': 'ChangePaymentValues',
        'change #payment_invoice_values': 'onChangePaymentInvoiceValues',
        'keyup #payment_invoice_values': 'onPaymentInvoiceValuesChange',
        'keypress #payment_values': 'onPaymentValuesKeyPress',
        'keypress #payment_invoice_values': 'onPaymentInvoiceValuesKeyPress',
    },

    onPaymentCheckboxChange: function (ev) {
        const $paymentValues = $('#payment_values');
        const isChecked = $(ev.currentTarget).is(':checked');
        jsonrpc("/check_partial_payment_order", {})
            .then(res => {
                const res1 = JSON.parse(res);
                if (res1.warning) {
                    $(ev.currentTarget).prop('checked', false);
                    $paymentValues.hide();
                    swal('You are not allowed to order more than ' + res1.max_partial_order + ' order, First please pay the Previous order.', "error");
                } else {
                    $paymentValues.toggle(isChecked);
                    if (isChecked) {
                        this.updatePaymentAmount('/sale/partial_pay/price', Number($paymentValues.val()));
                    } else {
                        $paymentValues.val($paymentValues.data('max'));
                        this.updatePaymentAmount('/sale/partial_pay/price', 0);
                    }
                }
            });
    },

    onInvoiceCheckboxChange: function (ev) {
        const $paymentInvoiceValues = $('#payment_invoice_values');
        const $Invoice = $("#invoice_id")
        const isChecked = $(ev.currentTarget).is(':checked');
        $paymentInvoiceValues.toggle(isChecked);
        if (isChecked) {
            this.updatePaymentAmountNew('/invoice/partial_pay/price', Number($paymentInvoiceValues.val()), $Invoice.val());
        } else {
            $paymentInvoiceValues.val($("#invoice_residual").val());
            this.updatePaymentAmountNew('/invoice/partial_pay/price', Number($("#invoice_residual").val()), $Invoice.val());
        }
    },

    onPaymentValuesChange: function (ev) {
        const $paymentValues = $('#payment_values');
        const max = parseFloat($paymentValues.data('max'));
        const currentVal = parseFloat($paymentValues.val());
        if (currentVal > max) {
            swal('You can not enter amount greater than ' + max, "", "error");
            $paymentValues.val(max.toFixed(2));
        }
        this.updatePaymentAmount('/sale/partial_pay/price', currentVal);
    },

    onPaymentInvoiceValuesChange: function (ev) {
        const $paymentInvoiceValues = $('#payment_invoice_values');
        const $Invoice = $("#invoice_id")
        const max = parseFloat($paymentInvoiceValues.data('max'));
        const currentVal = parseFloat($paymentInvoiceValues.val());
        if (currentVal > max) {
            swal('You can not enter amount greater than ' + max, "", "error");
            $paymentInvoiceValues.val(max.toFixed(2));
        }
        this.updatePaymentAmountNew('/invoice/partial_pay/price', currentVal, $Invoice.val());
    },

    ChangePaymentValues: function(ev) {
        let $currentTarget = $(ev.currentTarget);
        let max = parseFloat($currentTarget.data('max'));
        let currentValue = parseFloat($currentTarget.val());

        // Check if the entered value exceeds the maximum
        if(currentValue > max) {
            swal('You cannot enter an amount greater than ' + max, "", "error");
            $currentTarget.val(parseFloat(max).toFixed(2));
            currentValue = max;
        }

        // Check partial amount
        jsonrpc("/check_partial_amount", {
            'amount': currentValue
        }).then(result => {
            let res1 = JSON.parse(result);
            if (res1 && res1.warning) {
                $('#payment_values').val(parseFloat(max).toFixed(2));
                swal('You need to pay the '+res1.adv_payment_amount + "%", "of total order amount ", "error");
            }
        });

        // Update payment amount
        this.updatePaymentAmount('/sale/partial_pay/price', currentValue);
    },

    onChangePaymentInvoiceValues: function(ev) {
        const $paymentInvoiceValues = $('#payment_invoice_values');
        const $Invoice = $("#invoice_id")
        const max = parseFloat($paymentInvoiceValues.data('max'));
        const currentVal = parseFloat($paymentInvoiceValues.val());

        // Check if the entered value exceeds the maximum
        if (currentVal > max) {
            swal('You cannot enter an amount greater than ' + max, "", "error");
            $paymentInvoiceValues.val(max.toFixed(2));
            inputValue = max;
        }

        // Check for minimum payment term
        jsonrpc("/check_partial_payment_minimum_payment_term",  {
            'invoice_id': $Invoice.val(),
            'amount': currentVal
        }).then(res => {
            let res1 = JSON.parse(res);
            
            if (res1 && res1.warning) {
                $paymentInvoiceValues.val(max);
                swal('You need to pay all the remaining amount', "", "error");
            } else {
                // Update invoice payment amount
                this.updatePaymentAmountNew('/invoice/partial_pay/price', currentVal, $Invoice.val());
            }
        });
    },

    onPaymentValuesKeyPress: function (e) {
        if (e.which !== 8 && e.which !== 0 && e.which !== 46 && (e.which < 48 || e.which > 57)) {
            return false;
        }
    },

    onPaymentInvoiceValuesKeyPress: function (e) {
        if (e.which !== 8 && e.which !== 0 && e.which !== 46 && (e.which < 48 || e.which > 57)) {
            return false;
        }
    },

    updatePaymentAmount: function (endpoint, amount) {
        jsonrpc(endpoint, { amount });
    },

    updatePaymentAmountNew: function (endpoint, amount, invoice) {
        jsonrpc(endpoint, { amount, invoice });
    },
});
