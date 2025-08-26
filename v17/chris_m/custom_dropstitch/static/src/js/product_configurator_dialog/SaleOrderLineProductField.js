/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { SaleOrderLineProductField } from '@sale/js/sale_product_field';
import { ProductConfiguratorDialog } from "@sale_product_configurator/js/product_configurator_dialog/product_configurator_dialog";
import { serializeDateTime } from "@web/core/l10n/dates";
import { patch } from "@web/core/utils/patch";
import { x2ManyCommands } from "@web/core/orm_service";


//-----Custome changes-----
// handle custom values & no variants
// passed extra param customeAttrVals
// passed extra fields in update record
async function applyProduct(record, product, customeAttrVals) {

    const customAttributesCommands = [
        x2ManyCommands.set([]),  // Command.clear isn't supported in static_list/_applyCommands
    ];
    for (const ptal of product.attribute_lines) {
        const selectedCustomPTAV = ptal.attribute_values.find(
            ptav => ptav.is_custom && ptal.selected_attribute_value_ids.includes(ptav.id)
        );
        if (selectedCustomPTAV) {
            customAttributesCommands.push(
                x2ManyCommands.create(undefined, {
                    custom_product_template_attribute_value_id: [selectedCustomPTAV.id, "we don't care"],
                    custom_value: ptal.customValue,
                })
            );
        };
    }

    const noVariantPTAVIds = product.attribute_lines.filter(
        ptal => ptal.create_variant === "no_variant" && ptal.attribute_values.length > 1
    ).flatMap(ptal => ptal.selected_attribute_value_ids);

    await record.update({
        product_id: [product.id, product.display_name],
        product_uom_qty: product.quantity,
        product_no_variant_attribute_value_ids: [x2ManyCommands.set(noVariantPTAVIds)],
        product_custom_attribute_value_ids: customAttributesCommands,
        custom_line1: customeAttrVals.find((a) => Object.keys(a).indexOf('custom_line1') >= 0)['custom_line1'],
        custom_line2: customeAttrVals.find((a) => Object.keys(a).indexOf('custom_line2') >= 0)['custom_line2'],
        custom_line3: customeAttrVals.find((a) => Object.keys(a).indexOf('custom_line3') >= 0)['custom_line3'],
        custom_initials: customeAttrVals.find((a) => Object.keys(a).indexOf('custom_initials') >= 0)['custom_initials'],
        custom_personalize: customeAttrVals.find((a) => Object.keys(a).indexOf('custom_personalize') >= 0)['custom_personalize'],
    });
};


patch(SaleOrderLineProductField.prototype, {
    async _openProductConfigurator(edit = false) {
        const saleOrderRecord = this.props.record.model.root;
        let ptavIds = this.props.record.data.product_template_attribute_value_ids.records.map(
            record => record.resId
        );
        let customAttributeValues = [];
        let customeAttrVals = [];

        if (edit) {
            /**
             * no_variant and custom attribute don't need to be given to the configurator for new
             * products.
             */
            ptavIds = ptavIds.concat(this.props.record.data.product_no_variant_attribute_value_ids.records.map(
                record => record.resId
            ));
            /**
             *  `product_custom_attribute_value_ids` records are not loaded in the view bc sub templates
             *  are not loaded in list views. Therefore, we fetch them from the server if the record is
             *  saved. Else we use the value stored on the line.
             */
            customAttributeValues = this.props.record.data.product_custom_attribute_value_ids.records[0]?.isNew ?
                this.props.record.data.product_custom_attribute_value_ids.records.map(record => record.data) :
                await this.orm.read(
                    'product.attribute.custom.value',
                    this.props.record.data.product_custom_attribute_value_ids.currentIds,
                    ["custom_product_template_attribute_value_id", "custom_value"]
                )

        }
        // prepare custome attr values
        let record_data = this.props.record.data;
        customeAttrVals = [
            { 'custom_line1': record_data.custom_line1 },
            { 'custom_line2': record_data.custom_line2 },
            { 'custom_line3': record_data.custom_line3 },
            { 'custom_initials': record_data.custom_initials },
            { 'custom_personalize': record_data.custom_personalize }
        ]
        this.dialog.add(ProductConfiguratorDialog, {
            productTemplateId: this.props.record.data.product_template_id[0],
            ptavIds: ptavIds,
            customAttributeValues: customAttributeValues.map(
                data => {
                    return {
                        ptavId: data.custom_product_template_attribute_value_id[0],
                        value: data.custom_value,
                    }
                }
            ),
            customeAttrVals: customeAttrVals,
            quantity: this.props.record.data.product_uom_qty,
            productUOMId: this.props.record.data.product_uom[0],
            companyId: saleOrderRecord.data.company_id[0],
            pricelistId: saleOrderRecord.data.pricelist_id[0],
            currencyId: this.props.record.data.currency_id[0],
            soDate: serializeDateTime(saleOrderRecord.data.date_order),
            edit: edit,
            save: async (mainProduct, optionalProducts, customeAttrVals) => {
                await applyProduct(this.props.record, mainProduct, customeAttrVals);
                this._onProductUpdate();
                saleOrderRecord.data.order_line.leaveEditMode();
                for (const optionalProduct of optionalProducts) {
                    const line = await saleOrderRecord.data.order_line.addNewRecord({
                        position: 'bottom',
                        mode: "readonly",
                    });
                    await applyProduct(line, optionalProduct);
                }
            },
            discard: () => {
                saleOrderRecord.data.order_line.delete(this.props.record);
            },
        });
    },
});
