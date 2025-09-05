import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { Component, onMounted, useRef, useState } from "@odoo/owl";

export class RoutePickerPopup extends Component {
    static template = "point_of_sale.RoutePickerPopup";
    static components = { Dialog };
    static props = {
        current_route:{ type: String},
        routes:{ type: Object},
        title: { type: String, optional: true },
        confirmLabel: { type: String, optional: true },
        getPayload: Function,
        close: Function,
    };
    static defaultProps = {
        confirmLabel: _t("Confirm"),
        title: _t("Route Picker"),
    };

    setup() {
        super.setup();
        this.state = useState({
            shippingRoute: '', 
            current_route:this.props.current_route?parseInt(this.props.current_route):''
        });
        this.inputRef = useRef("select");
        onMounted(() => this.inputRef.el.focus());
    }
    confirm() {
        this.props.getPayload(this.inputRef.el.value?parseInt(this.inputRef.el.value):'');
        this.props.close();
    }
    _today() {
        return new Date().toISOString().split("T")[0];
    }
}
