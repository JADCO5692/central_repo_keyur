/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import publicWidget from "@web/legacy/js/public/public_widget"; 
import { rpc } from "@web/core/network/rpc"; 

publicWidget.registry.DocsToDown = publicWidget.Widget.extend({
    selector: '.docs_to_doenload',
    events: {
        'click #att_doc': '_OnDownload',
    },
    init() {
        this._super(...arguments);
        this.notification = this.bindService("notification");
        debugger
        // this.action = this.bindService("action");
    },
    start() {
        return this._super.apply(this, arguments);
    }, 
    _OnDownload(ev){
        debugger
        // this.action.doAction({
        // type: "ir.actions.act_window",
        // res_model: resModel,
        // views: [[this.formViewId, "form"]],
        // res_id: resId,
        // });
    }
});