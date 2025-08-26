/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";
import { getFormattedValue } from '@web/views/utils';

patch(ListRenderer.prototype, {
    getFormattedValue(column, record) {
        const fieldName = column.name;
        if (column.options.enable_formatting === false) {
            return record.data[fieldName];
        }
        if ((record.resModel == 'sale.order.line' && fieldName == 'product_uom_qty') ||
            (record.resModel == 'purchase.order.line' && fieldName == 'product_qty') ||
            (record.resModel == 'mrp.production' && fieldName == 'product_qty')) {
            return parseInt(getFormattedValue(record, fieldName, column.attrs).replace(',', ''));
        } else {
            return getFormattedValue(record, fieldName, column.attrs);
        }
    }
});