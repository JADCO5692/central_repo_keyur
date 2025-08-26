/** @odoo-module **/

import { FloatField } from '@web/views/fields/float/float_field';
import { patch } from "@web/core/utils/patch";

patch(FloatField.prototype, {
    parse(value) {
        if ((this.props.record.resModel == 'sale.order.line' && this.props.name == "product_uom_qty") ||
            (this.props.record.resModel == 'purchase.order.line' && this.props.name == "product_qty") ||
            (this.props.record.resModel == 'mrp.production' && ['qty_producing', 'product_qty'].includes(this.props.name))) {
            return this.props.inputType === "number" ? Number(value) : parseInt(value);
        } else {
            return this.props.inputType === "number" ? Number(value) : parseFloat(value);
        }

    },
    get formattedValue() {
        if ((this.props.record.resModel == 'sale.order.line' && this.props.name == "product_uom_qty") ||
            (this.props.record.resModel == 'purchase.order.line' && this.props.name == "product_qty") ||
            (this.props.record.resModel == 'mrp.production' && ['qty_producing', 'product_qty'].includes(this.props.name))) {
            if (!this.props.formatNumber || (this.props.inputType === "number" && !this.props.readonly && this.value)) {
                return this.value;
            }
            if (this.props.humanReadable && !this.state.hasFocus) {
                return parseInt(this.value, {
                    digits: this.digits,
                    humanReadable: true,
                    decimals: this.props.decimals,
                });
            } else {
                return parseInt(this.value, { digits: this.digits, humanReadable: false });
            }
        } else {
            return super.formattedValue;
        }

    }
});