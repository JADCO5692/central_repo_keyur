/** @odoo-module **/

import VariantMixin from "@website_sale/js/sale_variant_mixin";
import "@website_sale/js/website_sale";
import publicWidget from "@web/legacy/js/public/public_widget";

VariantMixin.handleCustomValues = function ($target) {
    var $variantContainer;
    var $customInput = false;
    if ($target.is('input[type=radio]') && $target.is(':checked')) {
        $variantContainer = $target.closest('ul').closest('li');
        $customInput = $target;
    } else if ($target.is('select')) {
        $variantContainer = $target.closest('li');
        $customInput = $target
            .find('option[value="' + $target.val() + '"]');
    }

    if ($variantContainer) {
        if ($customInput && $customInput.data('is_custom') === 'True') {
            var attributeValueId = $customInput.data('value_id');
            var attributeValueName = $customInput.data('value_name');

            if ($variantContainer.find('.variant_custom_value').length === 0 || $variantContainer.find('.variant_custom_value').data('custom_product_template_attribute_value_id') !== parseInt(attributeValueId)) {
                $variantContainer.find('.variant_custom_value').remove();
                // ***handled custome variant values***
                var line_number = $customInput.data('line_number');
                // to  be change if cust line fields increased
                if (!['=', 'Initials'].includes(attributeValueName)) {
                    if (line_number > 3) { line_number = 3; }
                    for (var i = 1; i <= line_number; i++) {
                        var $input = $('<input>', {
                            type: 'text',
                            'data-custom_product_template_attribute_value_id': attributeValueId,
                            'data-attribute_value_name': attributeValueName,
                            class: 'variant_custom_value form-control mt-2',
                            'data-field_name': "custom_line" + String(i)
                        });
                        $input.attr('placeholder', 'Line ' + String(i));
                        $input.addClass('custom_value_radio');
                        $variantContainer.append($input);
                    }
                } else {
                    let attr_field_name = '';
                    var placeholder = 'line';
                    if (attributeValueName == '=') {
                        attr_field_name = 'custom_personalize';
                        placeholder = 'Personalize';
                    } else if (attributeValueName == 'Initials') {
                        attr_field_name = 'custom_initials';
                        placeholder = 'Initials';
                    }
                    var $input = $('<input>', {
                        type: 'text',
                        'data-custom_product_template_attribute_value_id': attributeValueId,
                        'data-attribute_value_name': attributeValueName,
                        class: 'variant_custom_value form-control mt-2',
                        'data-field_name': attr_field_name
                    });
                    $input.attr('placeholder', placeholder);
                    $input.addClass('custom_value_radio');
                    $variantContainer.append($input);
                }
                // ***handled custome variant values***

                // const previousCustomValue = $customInput.attr("previous_custom_value");

                // if (previousCustomValue) {
                //     $input.val(previousCustomValue);
                // }
            }
        } else {
            $variantContainer.find('.variant_custom_value').remove();
        }
    }

};

publicWidget.registry.WebsiteSale.include({ 
    _onChangeCombination: function () {
        var res = this._super.apply(this, arguments);  
        var $parent = arguments[1];
        var combination = arguments[2];
        var rootComponentSelectors = [
            'tr.js_product',
            '.oe_website_sale',
            '.o_product_configurator'
        ];
        var isCombinationPossible = true;
        if (typeof combination.is_combination_possible !== "undefined") {
            isCombinationPossible = combination.is_combination_possible;
        }

        if(combination.mto_attribute_id){
            this._updateProductImage(
                $parent.closest(rootComponentSelectors.join(', ')),
                combination.display_image,
                combination.product_id,
                combination.product_template_id,
                combination.carousel,
                isCombinationPossible
            );
        }
    }, 
}); 

export default VariantMixin