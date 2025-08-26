/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ProductTemplateAttributeLine } from "@sale_product_configurator/js/product_template_attribute_line/product_template_attribute_line";

patch(ProductTemplateAttributeLine, {
    template: 'saleProductConfigurator.ptal-custom',
    props: {
        productTmplId: Number,
        id: Number,
        attribute: {
            type: Object,
            shape: {
                id: Number,
                name: String,
                display_type: {
                    type: String,
                    validate: type => ["color", "multi", "pills", "radio", "select"].includes(type),
                },
            },
        },
        attribute_values: {
            type: Array,
            element: {
                type: Object,
                shape: {
                    id: Number,
                    name: String,
                    html_color: [Boolean, String], // backend sends 'false' when there is no color
                    image: [Boolean, String], // backend sends 'false' when there is no image set
                    is_custom: Boolean,
                    price_extra: Number,
                    line_number: Number,
                    excluded: { type: Boolean, optional: true },
                },
            },
        },
        selected_attribute_value_ids: { type: Array, element: Number },
        create_variant: {
            type: String,
            validate: type => ["always", "dynamic", "no_variant"].includes(type),
        },
        customValue: { type: [{ value: false }, String], optional: true },
    }
});

patch(ProductTemplateAttributeLine.prototype, {
    setup() {
        super.setup();
    },
    GetInputCount(event) {
        var selected_attr_id = this.props.selected_attribute_value_ids[0];
        var ptv_value = this.props.attribute_values.filter((i) => i.id == selected_attr_id);
        return ptv_value.length ? ptv_value[0] : [];
    },
    get_field_value(field) {
        return this.env.getCustomValues().find((a) => Object.keys(a).indexOf(field) >= 0)[field]
    },
    get_field_name(attr) {
        if (attr.name == '=') {
            return 'custom_personalize';
        }
        else if (attr.name == 'Initials') {
            return 'custom_initials';
        } else {
            return 'custom_line1';
        }
    },
    _updatePTAVCustomLineValue(event) {
        var field = $(event.currentTarget).data().field;
        var value = $(event.currentTarget).val();
        this.env.updatePTAVCustomLineValue(field, value)
    }
})