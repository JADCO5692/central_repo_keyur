/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { ProductConfiguratorDialog } from "@sale_product_configurator/js/product_configurator_dialog/product_configurator_dialog";
import { patch } from "@web/core/utils/patch";
// import { SaleOrderLineProductField } from '@sale/js/sale_product_field';
import { useSubEnv } from "@odoo/owl";

// added @customeAttrVals in props

patch(ProductConfiguratorDialog, {
    props: {
        productTemplateId: Number,
        ptavIds: { type: Array, element: Number },
        customAttributeValues: {
            type: Array,
            element: Object,
            shape: {
                ptavId: Number,
                value: String,
            }
        },
        customeAttrVals: {
            type: Array,
            element: Object,
            shape: {
                line_field: String,
                value: String,
            }
        },
        quantity: Number,
        productUOMId: { type: Number, optional: true },
        companyId: { type: Number, optional: true },
        pricelistId: { type: Number, optional: true },
        currencyId: Number,
        soDate: String,
        edit: { type: Boolean, optional: true },
        save: Function,
        discard: Function,
        close: Function, // This is the close from the env of the Dialog Component
    }
});
patch(ProductConfiguratorDialog.prototype, {
    setup() {
        super.setup();
        // added updatePTAVCustomLineValue to the subEnv
        useSubEnv({
            mainProductTmplId: this.props.productTemplateId,
            currencyId: this.props.currencyId,
            addProduct: this._addProduct.bind(this),
            removeProduct: this._removeProduct.bind(this),
            setQuantity: this._setQuantity.bind(this),
            updateProductTemplateSelectedPTAV: this._updateProductTemplateSelectedPTAV.bind(this),
            updatePTAVCustomValue: this._updatePTAVCustomValue.bind(this),
            isPossibleCombination: this._isPossibleCombination,
            updatePTAVCustomLineValue: this._updatePTAVCustomLineValue.bind(this),
            getCustomValues: this._getCustomValues.bind(this),
        });
    },
    async onConfirm() {
        if (!this.isPossibleConfiguration()) return;
        if (!this.checkCustomValues(event)) return;
        // Create the products with dynamic attributes
        for (const product of this.state.products) {
            if (
                !product.id &&
                product.attribute_lines.some(ptal => ptal.create_variant === "dynamic")
            ) {
                const productId = await this._createProduct(product);
                product.id = parseInt(productId);
            }
        }
        await this.props.save(
            this.state.products.find(
                p => p.product_tmpl_id === this.env.mainProductTmplId
            ),
            this.state.products.filter(
                p => p.product_tmpl_id !== this.env.mainProductTmplId
            ),
            this.props.customeAttrVals
        );
        this.props.close();
    },
    checkCustomValues(ev) {
        let $target = $(ev.currentTarget).parents('.modal-content').find('.cst-vals-container');
        let isValid = true;
        $target.find('input.o_input').each(function () {
            if ($(this).val() == '') {
                isValid = false;
                $(this).addClass('o_field_invalid');
            } else {
                $(this).removeClass('o_field_invalid');
            }
        })
        return isValid;
    },
    _updatePTAVCustomLineValue(field_name, customValue) {
        this.props.customeAttrVals.find((a) => Object.keys(a).indexOf(field_name) >= 0)[field_name] = customValue
    },
    _getCustomValues() {
        return this.props.customeAttrVals
    }
}); 