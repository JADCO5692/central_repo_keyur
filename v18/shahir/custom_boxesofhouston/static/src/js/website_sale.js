/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import publicWidget from "@web/legacy/js/public/public_widget"; 
import { rpc } from "@web/core/network/rpc";
let added_to_quote_ele = '<a href="javascript:;" role="button" class="btn btn-primary a-quote" aria-label="Request A Quote" title="Added to Quote" > Added to Quote </a>'

publicWidget.registry.WebsiteSale.include({
    events: Object.assign({}, publicWidget.registry.WebsiteSale.prototype.events, {
        'click a.o_quote_product_btn': '_on_create_quote',
    }),
    init() {
        this._super(...arguments);
        this.notification = this.bindService("notification");
    },
    start() {
        return this._super.apply(this, arguments);
    },
    _on_create_quote: async function (ev) {
        let self = this;
        let $parent = $(ev.currentTarget).parents('form');
        let product_id = $parent.find("input[name='product_id']")?.val();
        let product_template_id = $parent.find("input[name='product_template_id']")?.val();
        let qty = $parent.find('inpute.quantity')?.val();
        await rpc('/create/quote',
        {
            'product_id': product_id, 
            'qty': qty?qty:0,
        }).then((data) => {
            if (data.success) {
                $parent.find('.o_quote_product_btn').replaceWith(added_to_quote_ele);
                self.notification.add('Added succesfully', {
                    type: "warning",
                    sticky: false,
                    title: _t("Product added to quotation."),
                });
            }
        });
    }
});