/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { qrCodeSrc } from "@point_of_sale/utils";
import { OnlinePaymentPopup } from "@pos_online_payment/app/online_payment_popup/online_payment_popup";


patch(PaymentScreen.prototype, {
    async _isOrderValid(isForceValidate) {
        if (!(await super._isOrderValid(...arguments))) {
            return false;
        }

        if (!this.payment_methods_from_config.some((pm) => pm.is_online_payment)) {
            return true;
        }

        if (this.currentOrder.finalized) {
            this.afterOrderValidation(false);
            return false;
        }

        const onlinePaymentLines = this.getRemainingOnlinePaymentLines();
        if (onlinePaymentLines.length > 0) {
            if (!this.currentOrder.id) {
                this.cancelOnlinePayment(this.currentOrder);
                this.dialog.add(AlertDialog, {
                    title: _t("Online payment unavailable"),
                    body: _t("The QR Code for paying could not be generated."),
                });
                return false;
            }
            let prevOnlinePaymentLine = null;
            let lastOrderServerOPData = null;
            for (const onlinePaymentLine of onlinePaymentLines) {
                const onlinePaymentLineAmount = onlinePaymentLine.get_amount();
                // The local state is not aware if the online payment has already been done.
                lastOrderServerOPData = await this.pos.update_online_payments_data_with_server(
                    this.currentOrder,
                    onlinePaymentLineAmount
                );
                if (!lastOrderServerOPData) {
                    this.dialog.add(AlertDialog, {
                        title: _t("Online payment unavailable"),
                        body: _t(
                            "There is a problem with the server. The order online payment status cannot be retrieved."
                        ),
                    });
                    return false;
                }
                if (!lastOrderServerOPData.is_paid) {
                    if (lastOrderServerOPData.modified_payment_lines) {
                        this.cancelOnlinePayment(this.currentOrder);
                        this.dialog.add(AlertDialog, {
                            title: _t("Updated online payments"),
                            body: _t("There are online payments that were missing in your view."),
                        });
                        return false;
                    }
                    if (
                        (prevOnlinePaymentLine &&
                            prevOnlinePaymentLine?.get_payment_status() !== "done") ||
                        !this.checkRemainingOnlinePaymentLines(lastOrderServerOPData.amount_unpaid)
                    ) {
                        this.cancelOnlinePayment(this.currentOrder);
                        return false;
                    }

                    onlinePaymentLine.set_payment_status("waiting");
                    this.currentOrder.select_paymentline(onlinePaymentLine);
                    const onlinePaymentData = {
                        formattedAmount: this.env.utils.formatCurrency(onlinePaymentLineAmount),
                        qrCode: qrCodeSrc(
                            `${this.pos.session._base_url}/pos/pay/${this.currentOrder.id}?access_token=${this.currentOrder.access_token}`
                        ),
 paymentUrl:`${this.pos.session._base_url}/pos/pay/${this.currentOrder.id}?access_token=${this.currentOrder.access_token}`,
                        orderName: this.currentOrder.name,
                    };
                    this.currentOrder.onlinePaymentData = onlinePaymentData;
                    const qrCodePopupCloser = this.dialog.add(
                        OnlinePaymentPopup,
                        onlinePaymentData,
                        {
                            onClose: () => {
                                onlinePaymentLine.onlinePaymentResolver(false);
                            },
                        }
                    );
                    const paymentResult = await new Promise(
                        (r) => (onlinePaymentLine.onlinePaymentResolver = r)
                    );
                    if (!paymentResult) {
                        this.cancelOnlinePayment(this.currentOrder);
                        onlinePaymentLine.set_payment_status(undefined);
                        return false;
                    }
                    qrCodePopupCloser();
                    if (onlinePaymentLine.get_payment_status() === "waiting") {
                        onlinePaymentLine.set_payment_status(undefined);
                    }
                    prevOnlinePaymentLine = onlinePaymentLine;
                }
            }

            if (!lastOrderServerOPData || !lastOrderServerOPData.is_paid) {
                lastOrderServerOPData = await this.pos.update_online_payments_data_with_server(
                    this.currentOrder,
                    0
                );
            }
            if (!lastOrderServerOPData || !lastOrderServerOPData.is_paid) {
                return false;
            }

            await this.afterPaidOrderSavedOnServer(lastOrderServerOPData.paid_order);
            return false; // Cancel normal flow because the current order is already saved on the server.
        } else if (typeof this.currentOrder.id === "number") {
            const orderServerOPData = await this.pos.update_online_payments_data_with_server(
                this.currentOrder,
                0
            );
            if (!orderServerOPData) {
                return ask(this.dialog, {
                    title: _t("Online payment unavailable"),
                    body: _t(
                        "There is a problem with the server. The order online payment status cannot be retrieved. Are you sure there is no online payment for this order ?"
                    ),
                    confirmLabel: _t("Yes"),
                });
            }
            if (orderServerOPData.is_paid) {
                await this.afterPaidOrderSavedOnServer(orderServerOPData.paid_order);
                return false; // Cancel normal flow because the current order is already saved on the server.
            }
            if (orderServerOPData.modified_payment_lines) {
                this.dialog.add(AlertDialog, {
                    title: _t("Updated online payments"),
                    body: _t("There are online payments that were missing in your view."),
                });
                return false;
            }
        }

        return true;
    },
});
