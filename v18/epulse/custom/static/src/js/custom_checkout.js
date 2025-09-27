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

        const btn = ev.currentTarget;
        // Save original text
        const originalText = btn.innerHTML;

        // Disable button + show loader
        btn.disabled = true;
        btn.innerHTML = `Processing... <span class="loader"></span>`;
        const cargo_location = document.querySelector("[name='cargo_location']")?.value || "";
        const cargo_instructions = document.querySelector("[name='cargo_instructions']")?.value || "";

        rpc('/custom/custom_checkout', {
        cargo_location: cargo_location,
        cargo_instructions: cargo_instructions
        })  // Use rpc directly for Odoo 18
            .then((response) => {
                if (response.redirect_url) {
                    window.location.href = response.redirect_url;
                } else {
                    console.error("Error: No redirect URL received.");
                    // Restore button if no redirect
                    btn.disabled = false;
                    btn.innerHTML = originalText;
                }
            })
            .catch((error) => {
                console.error("Error sending email:", error);
                // Restore button on error
                btn.disabled = false;
                btn.innerHTML = originalText;
            });
    },
});

publicWidget.registry.SendEmailRedirect = SendEmailRedirect;

export default {
    SendEmailRedirect: publicWidget.registry.SendEmailRedirect,
};