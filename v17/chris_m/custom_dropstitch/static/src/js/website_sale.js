/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import "@website_sale/js/website_sale";
import { post } from "@web/core/network/http_service";

publicWidget.registry.WebsiteSale.include({
    events: Object.assign({}, publicWidget.registry.WebsiteSale.prototype.events || {}, {
        "input input[name='image_upload']": '_OnChangeImageUpload',
        "click a[name='website_sale_main_button']": '_OnclickCheckout'
    }),
    init: function () {
        this._super.apply(this, arguments);
        this.orm = this.bindService("orm");
    },
    /**
     * Adds product sku to the products details
     * @override
     */
    _onChangeCombination: function () {
        this._super.apply(this, arguments);
        let custom_customer_sku = arguments[2].custom_customer_sku;
        let custom_prod_size = arguments[2].custom_prod_size;
        let custom_fiber = arguments[2].custom_fiber;
        let custom_weight = arguments[2].weight;
        debugger
        if (custom_customer_sku) {
            this.$target.find('.custom_customer_sku').html('Customer SKU : ' + custom_customer_sku);
        }
        else {
            this.$target.find('.custom_customer_sku').empty()
        }
        if (custom_prod_size) {
            this.$target.find('.o-line-custom_prod_size').removeClass('d-none');
            this.$target.find('.o-line-custom_prod_size').html('<b class="pe-1">Size </b>  : ' + custom_prod_size);
        }
        else { 
            this.$target.find('.o-line-custom_prod_size').empty().addClass('d-none');
        }
        if (custom_fiber) {
            this.$target.find('.o-line-custom_fiber').removeClass('d-none');
            this.$target.find('.o-line-custom_fiber').html('<b class="pe-1">Fiber </b>    : ' + custom_fiber);
        }
        else {
            this.$target.find('.o-line-custom_fiber').empty().addClass('d-none');
        }
        if (custom_weight) {
            this.$target.find('.o-line-weight').removeClass('d-none');
            this.$target.find('.o-line-weight').html('<b class="pe-1">Weight </b>   : ' + custom_weight);
        }
        else {
            this.$target.find('.o-line-weight').empty().addClass('d-none');
        } 
        if (arguments[2]?.yarn_component_images) {
            $('.yarn-component-container').html(arguments[2]?.yarn_component_images);
        }
    },
    _updateRootProduct($form, productId) {
        this.rootProduct = {
            product_id: productId,
            quantity: parseFloat($form.find('input[name="add_qty"]').val() || 1),
            product_custom_attribute_values: this.getCustomVariantValues1($form.find('.js_product')),
            variant_values: this.getSelectedVariantValues($form.find('.js_product')),
            no_variant_attribute_values: this.getNoVariantAttributeValues($form.find('.js_product'))
        };
    },
    getCustomVariantValues1($container) {
        var variantCustomValues = [];
        $container.find('.variant_custom_value').each(function () {
            var $variantCustomValueInput = $(this);
            if ($variantCustomValueInput.length !== 0) {
                var field_name = $variantCustomValueInput.data('field_name');
                variantCustomValues.push({
                    'custom_product_template_attribute_value_id': $variantCustomValueInput.data('custom_product_template_attribute_value_id'),
                    'attribute_value_name': $variantCustomValueInput.data('attribute_value_name'),
                    'custom_value': $variantCustomValueInput.val(),
                    field_name: $variantCustomValueInput.data('field_name')
                });
                // removed custome_value => '', $variantCustomValueInput.val()
            }
        });
        return variantCustomValues
    },
    _onClickAdd: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        let isValidate = true;
        $(this.el).find('.variant_custom_value').each(function () {
            let value = $(this)?.val() || '';
            if (value.trim() == '') {
                isValidate = false;
                $(this).addClass('border-danger');
            } else {
                $(this).removeClass('border-danger');
                isValidate = true;
            }
        })
        if (!isValidate) {
            return false;
        } else {
            return this._super.apply(this, arguments);
        }
    },
    _submitForm: async function () {
        var res = await this._super.apply(this, arguments);
        if (res.line_id) {
            var $target = $(this.el);
            var input_image = $target.find('.img-file-upload input[name="image_upload"]');
            var input_tiff = $target.find('.tiff-file-upload input[name="tiff_upload"]');
            var line_ref = $target.find('.o-line-ref .o-line-reference').val();
            const formData = new FormData();
            formData.append('line_id', res.line_id);
            formData.append('line_ref', line_ref);
            formData.append('image_file', input_image.length && input_image[0].files[0] ? input_image[0].files[0] : '');
            formData.append('tiff_file', input_tiff.length && input_tiff[0].files[0] ? input_tiff[0].files[0] : '');
            formData.append('tiff_file_name', input_tiff.length && input_tiff[0].files[0] ? input_tiff[0].files[0]?.name : '');
            if (input_image || input_tiff) {
                await post('/line/update_inputs', formData);
            }
            $target.find('.img-file-upload input[name="image_upload"]')?.val('');
            $target.find('.tiff-file-upload input[name="tiff_upload"]')?.val('');
            $target.find('.image_upload_preview').css("background-image", "");
            $target.find('.o-line-ref .o-line-reference')?.val('');
            return res
        } else {
            return res;
        }
    },
    _OnChangeImageUpload: function (ev) {
        var uploadFile = $(ev.currentTarget);
        var files = !!ev.currentTarget.files ? ev.currentTarget.files : [];
        if (!files.length || !window.FileReader) return; // no file selected, or no FileReader support

        if (/^image/.test(files[0].type)) { // only image file
            var reader = new FileReader(); // instance of the FileReader
            reader.readAsDataURL(files[0]); // read the local file

            reader.onloadend = function () { // set image data as background of div
                // alert(uploadFile.closest(".file-upload").find('.imagePreview').length);
                uploadFile.parents("#product_detail").find('.image_upload_preview').css("background-image", "url(" + this.result + ")").addClass("d-block");
            }
        } else {
            uploadFile.parents("#product_detail").find('.image_upload_preview').removeClass("d-block");
        }
    },
    _OnclickCheckout: async function (e) {
        e.preventDefault();
        e.stopPropagation();
        var href = e.currentTarget.href;
        var order_id = e.currentTarget.dataset.soid;
        var $inputOref = $(e.currentTarget).parents('.card-body').find("input[name='customer_ord_ref']");
        var $inputSpecialInst = $(e.currentTarget).parents('.card-body').find("input[name='customer_special_instructions']");
        if($inputOref.length){
            if ($inputOref.val().trim(' ') != '' && order_id) {
                $inputOref.removeClass('is-invalid');
                let client_order_ref = $inputOref.val() || false;
                let inputSpecialInst = $inputSpecialInst.val() || false;'';
                await this.orm.call('sale.order', 'custom_client_order_ref', [parseInt(order_id)], {client_order_ref: client_order_ref, custom_so_special_inst: inputSpecialInst}).then(() => {
                    window.location = href;;
                })
            } else {
                if (!$inputOref.hasClass('is-invalid')) {
                    $inputOref.addClass('is-invalid');
                }
                return false;
            }
        }
        else {
            window.location = href;
        }
    }
});
