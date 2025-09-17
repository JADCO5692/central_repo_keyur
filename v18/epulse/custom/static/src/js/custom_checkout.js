/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";  // Import the rpc module
export const SendEmailRedirect = publicWidget.Widget.extend({
    selector: '#send_email_redirect',
    events: {
        'click': '_onClickSendEmail',
    },

    start: function () {
        console.log("SendEmailRedirect widget initialized");
        return this._super.apply(this, arguments);
    },

    _onClickSendEmail: function (ev) {
        console.log("Send Email & Redirect button clicked");
        ev.preventDefault();

        rpc('/custom/custom_checkout', {})  // Use rpc directly for Odoo 18
            .then((response) => {
                if (response.redirect_url) {
                    window.location.href = response.redirect_url;
                } else {
                    console.error("Error: No redirect URL received.");
                }
            })
            .catch((error) => {
                console.error("Error sending email:", error);
            });
    },
});

publicWidget.registry.SendEmailRedirect = SendEmailRedirect;

export default {
    SendEmailRedirect: publicWidget.registry.SendEmailRedirect,
};