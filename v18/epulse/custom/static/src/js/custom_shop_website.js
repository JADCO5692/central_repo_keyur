/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { Dialog } from "@web/core/dialog/dialog";

export const PinDialog = publicWidget.Widget.extend({
    selector: 'a[href="/shop"]',
    events: {
        'click': '_onShopLinkClick',
    },

    start: function () {
        console.log("PinDialog------d");
        return this._super.apply(this, arguments);
    },

    _onShopLinkClick: function (ev) {
        ev.preventDefault();
        console.log("Shop menu clicked");
       const dialog = new Dialog(this, {
            title: 'Shop Dialog',
            size: 'medium',
            $content: $('<p>Welcome to the shop!</p>'),
            buttons: [
                { text: 'Close', close: true }
            ],
        });
        dialog.open();
    },
});
