from odoo import http, _
import json
from odoo.http import request, route
from odoo.addons.website_sale.controllers import main

from odoo.addons.website_sale.controllers.variant import WebsiteSaleVariantController 
from odoo import SUPERUSER_ID  
from odoo.exceptions import ValidationError 

class WebsiteSaleStockVariantController(WebsiteSaleVariantController):

    @route(
        "/website_sale/get_combination_info",
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def get_combination_info_website(
        self,
        product_template_id,
        product_id,
        combination,
        add_qty,
        parent_combination=None,
        **kwargs
    ):
        product_template = request.env["product.template"].browse(
            product_template_id and int(product_template_id)
        )

        combination_info = product_template._get_combination_info(
            combination=request.env["product.template.attribute.value"].browse(
                combination
            ),
            product_id=product_id and int(product_id),
            add_qty=add_qty and float(add_qty) or 1.0,
            parent_combination=request.env["product.template.attribute.value"].browse(
                parent_combination
            ),
        )

        # Pop data only computed to ease server-side computations.
        for key in ("product_taxes", "taxes", "currency", "date"):
            combination_info.pop(key)

        if (
            request.website.product_page_image_width != "none"
            and not request.env.context.get("website_sale_no_images", False)
        ):
            special_attributes = (
                request.env["product.template.attribute.value"]
                .browse(combination)
                .filtered(lambda a: a.attribute_id.is_special_mto_attr)
            )
            mto_attribute = False
            if (
                len(special_attributes)
                and special_attributes.product_attribute_value_id
            ):
                mto_attribute = special_attributes.product_attribute_value_id

            # yarn compoentns
            yarn_attrib_ids = (
                request.env["product.template.attribute.value"]
                .sudo()
                .browse(combination)
                .filtered(lambda a: a.attribute_id.show_yarn_component_image)
            )
            if len(yarn_attrib_ids):
                yarn_component_ids = [
                    [
                        i.product_attribute_value_id.custom_product_component.id,
                        i.product_attribute_value_id.custom_product_component.display_name,
                    ]
                    for i in yarn_attrib_ids
                ]

                combination_info["yarn_component_images"] = request.env[
                    "ir.ui.view"
                ]._render_template(
                    "custom_dropstitch.yarn_compoentn_images",
                    values={"yarn_components": yarn_component_ids},
                )

            combination_info["carousel"] = request.env["ir.ui.view"]._render_template(
                "website_sale.shop_product_images",
                values={
                    "product": product_template,
                    "product_variant": request.env["product.product"].browse(
                        combination_info["product_id"]
                    ),
                    "website": request.env["website"].get_current_website(),
                    "mto_attribute_id": mto_attribute.id if mto_attribute else False,
                },
            )
            combination_info["mto_attribute_id"] = (
                mto_attribute.id if mto_attribute else False
            )
        return combination_info


class WebsiteSaleInh(main.WebsiteSale):

    @http.route(
        ["/shop/cart/update_json"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=False,
    )
    def cart_update_json(
        self,
        product_id,
        line_id=None,
        add_qty=None,
        set_qty=None,
        display=True,
        product_custom_attribute_values=None,
        no_variant_attribute_values=None,
        **kw
    ):
        # remove custome values and call base flow.
        temp_ptav = (
            json.loads(product_custom_attribute_values)
            if product_custom_attribute_values
            else []
        )
        if temp_ptav and len(temp_ptav) > 1:
            product_custom_attribute_values = json.dumps([temp_ptav[0]])
            # product_custom_attribute_values = json.dumps([json.loads(attrib_custom_values)[0]])
        res = super(WebsiteSaleInh, self).cart_update_json(
            product_id,
            line_id,
            add_qty,
            set_qty,
            display,
            product_custom_attribute_values,
            no_variant_attribute_values,
            **kw
        )
        # Write custome fields values to order line
        if product_custom_attribute_values:
            sale_order = request.website.sale_get_order()
            line_id = res.get("line_id")
            # print(attrib_custom_values)
            if line_id and sale_order.order_line:
                order_line_obj = sale_order.order_line.browse(line_id)
                if len(order_line_obj):
                    for atv in temp_ptav:
                        order_line_obj.write(
                            {atv.get("field_name"): atv.get("custom_value")}
                        )
                    # print(order_line_obj.read(fields=['id','custom_line1','custom_line2','custom_line3']))
        return res

    @route(
        "/shop/cart/update_option",
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
        multilang=False,
    )
    def cart_options_update_json(self, product_and_options, lang=None, **kwargs):
        if lang:
            request.website = request.website.with_context(lang=lang)

        order = request.website.sale_get_order(force_create=True)
        if order.state != "draft":
            request.session["sale_order_id"] = None
            order = request.website.sale_get_order(force_create=True)

        product_and_options = json.loads(product_and_options)
        if product_and_options:
            # The main product is the first, optional products are the rest
            main_product = product_and_options[0]
            values = order._cart_update(
                product_id=main_product["product_id"],
                add_qty=main_product["quantity"],
                product_custom_attribute_values=[],
                no_variant_attribute_values=main_product["no_variant_attribute_values"],
                **kwargs
            )

            # custom-------
            if values.get("line_id"):
                order_line_obj = order.order_line.browse(values.get("line_id"))
                custom_atr_values = product_and_options[0].get(
                    "product_custom_attribute_values"
                )
                if len(custom_atr_values):
                    for attr_value in custom_atr_values:
                        order_line_obj.write(
                            {
                                attr_value.get("field_name"): attr_value.get(
                                    "custom_value"
                                )
                            }
                        )
            # custom-------
            line_ids = [values["line_id"]]
            if values["line_id"]:
                # Link option with its parent iff line has been created.
                option_parent = {main_product["unique_id"]: values["line_id"]}
                for option in product_and_options[1:]:
                    parent_unique_id = option["parent_unique_id"]
                    option_values = order._cart_update(
                        product_id=option["product_id"],
                        set_qty=option["quantity"],
                        linked_line_id=option_parent[parent_unique_id],
                        product_custom_attribute_values=option[
                            "product_custom_attribute_values"
                        ],
                        no_variant_attribute_values=option[
                            "no_variant_attribute_values"
                        ],
                        **kwargs
                    )
                    option_parent[option["unique_id"]] = option_values["line_id"]
                    line_ids.append(option_values["line_id"])

            values["notification_info"] = self._get_cart_notification_information(
                order, line_ids
            )

        values["cart_quantity"] = order.cart_quantity
        request.session["website_sale_cart_quantity"] = order.cart_quantity

        return values


    @http.route('/shop/payment/validate', type='http', auth="public", website=True, sitemap=False)
    def shop_payment_validate(self, sale_order_id=None, **post):
        """ Method that should be called by the server when receiving an update
        for a transaction. State at this point :

         - UDPATE ME
        """
        if sale_order_id is None:
            order = request.website.sale_get_order()
            if not order and 'sale_last_order_id' in request.session:
                # Retrieve the last known order from the session if the session key `sale_order_id`
                # was prematurely cleared. This is done to prevent the user from updating their cart
                # after payment in case they don't return from payment through this route.
                last_order_id = request.session['sale_last_order_id']
                order = request.env['sale.order'].sudo().browse(last_order_id).exists()
        else:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            assert order.id == request.session.get('sale_last_order_id')

        errors = self._get_shop_payment_errors(order)
        if errors:
            first_error = errors[0]  # only display first error
            error_msg = f"{first_error[0]}\n{first_error[1]}"
            raise ValidationError(error_msg)

        tx_sudo = order.get_portal_last_transaction() if order else order.env['payment.transaction']

        if not order or (order.amount_total and not tx_sudo and order.get_discount_amount() != 0):
            return request.redirect('/shop')

        if order and (not order.amount_total or not order.get_discount_amount() != 0) and not tx_sudo:
            if order.state != 'sale':
                order.with_context(send_email=True).with_user(SUPERUSER_ID).action_confirm()
            request.website.sale_reset()
            return request.redirect(order.get_portal_url())

        # clean context and session, then redirect to the confirmation page
        request.website.sale_reset()
        if tx_sudo and tx_sudo.state == 'draft':
            return request.redirect('/shop')

        return request.redirect('/shop/confirmation')
    
    @http.route(['/shop/payment'], type='http', auth="public", website=True)
    def shop_payment(self, **post):
        provider = request.env['payment.provider']
        p_method = request.env['payment.method']
        res = super(WebsiteSaleInh, self).shop_payment(**post)
        order = res.qcontext.get('website_sale_order')
        if order and not order.get_discount_amount():
            res.qcontext['providers_sudo'] = provider
            res.qcontext['payment_methods_sudo'] = p_method 
        return res