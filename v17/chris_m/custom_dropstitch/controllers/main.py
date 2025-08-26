# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from datetime import datetime
from odoo.http import request
from odoo.addons.sale_product_configurator.controllers.main import (
    ProductConfiguratorController,
)
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.osv import expression
from werkzeug.exceptions import NotFound
from odoo.exceptions import UserError
from odoo.addons.sale.controllers.portal import CustomerPortal
from odoo.addons.aspl_website_partial_payment_ee.controllers.main import WebsitePartialPayment
from odoo.addons.payment.controllers import portal as payment_portal 
from odoo.exceptions import AccessError, ValidationError, UserError
from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing 
import json
import base64
import io
import logging

_logger = logging.getLogger(__name__)


class ProductConfiguratorControllerInherit(ProductConfiguratorController):
    def _get_product_information(
        self,
        product_template,
        combination,
        currency_id,
        so_date,
        quantity=1,
        product_uom_id=None,
        pricelist_id=None,
        parent_combination=None,
    ):
        pricelist = request.env["product.pricelist"].browse(pricelist_id)
        product_uom = request.env["uom.uom"].browse(product_uom_id)
        currency = request.env["res.currency"].browse(currency_id)
        product = product_template._get_variant_for_combination(combination)
        attribute_exclusions = product_template._get_attribute_exclusions(
            parent_combination=parent_combination, combination_ids=combination.ids
        )

        return dict(
            product_tmpl_id=product_template.id,
            **self._get_basic_product_information(
                product or product_template,
                pricelist,
                combination,
                quantity=quantity,
                uom=product_uom,
                currency=currency,
                date=datetime.fromisoformat(so_date),
            ),
            quantity=quantity,
            attribute_lines=[
                dict(
                    id=ptal.id,
                    attribute=dict(
                        **ptal.attribute_id.read(["id", "name", "display_type"])[0]
                    ),
                    attribute_values=[
                        dict(
                            **ptav.read(
                                [
                                    "name",
                                    "html_color",
                                    "image",
                                    "is_custom",
                                    "line_number",
                                ]
                            )[0],
                            price_extra=ptav.currency_id._convert(
                                ptav.price_extra,
                                currency,
                                request.env.company,
                                datetime.fromisoformat(so_date).date(),
                            ),
                        )
                        for ptav in ptal.product_template_value_ids
                        if ptav.ptav_active
                        or combination
                        and ptav.id in combination.ids
                    ],
                    selected_attribute_value_ids=combination.filtered(
                        lambda c: ptal in c.attribute_line_id
                    ).ids,
                    create_variant=ptal.attribute_id.create_variant,
                )
                for ptal in product_template.attribute_line_ids
            ],
            exclusions=attribute_exclusions["exclusions"],
            archived_combinations=attribute_exclusions["archived_combinations"],
            parent_exclusions=attribute_exclusions["parent_exclusions"],
        )


class WebsiteSaleInherit(WebsiteSale):
    def _get_search_domain(self, *args, **kwargs):
        super_domain = super(WebsiteSaleInherit, self)._get_search_domain(
            *args, **kwargs
        )
        if request.env.user.has_group("base.group_portal"):
            if request.env.user.partner_id.custom_allowed_customer_ids:
                domain = [
                    ("is_published", "=", True),
                    ("sale_ok", "=", True),
                    "|","|","|",
                    ('custom_allowed_customer_ids', '=', request.env.user.partner_id.id),
                    ("custom_link_customer", "=", request.env.user.partner_id.id),
                    ("custom_link_customer", "=", False),
                    (
                        "custom_link_customer",
                        "in",
                        request.env.user.partner_id.custom_allowed_customer_ids.ids,
                    ),
                ]
            else:
                domain = [
                    ("is_published", "=", True),
                    ("sale_ok", "=", True),
                    "|","|",
                    ('custom_allowed_customer_ids', '=', request.env.user.partner_id.id),
                    ("custom_link_customer", "=", request.env.user.partner_id.id),
                    ("custom_link_customer", "=", False),
                ]
            return expression.AND([domain, super_domain])
        else:
            return super_domain

    @http.route(
        ['/shop/<model("product.template"):product>'],
        type="http",
        auth="public",
        website=True,
        sitemap=True,
    )
    def product(self, product, category="", search="", **kwargs):
        if not self.check_user_access():
            return request.redirect("/web/login")

        request.env.registry.clear_cache()
        custom_allowed_customer_ids = (
            request.env.user.partner_id.custom_allowed_customer_ids.ids
        )
        custom_allowed_customer_ids.append(request.env.user.partner_id.id)
        custom_allowed_customer_ids.append(False)

        if (
            request.env.user.has_group("base.group_portal")
            and request.env.user.partner_id
            and ( product.custom_link_customer.id not in custom_allowed_customer_ids and request.env.user.partner_id.id not in product.custom_allowed_customer_ids.ids )
        ):
            raise NotFound()
        return super().product(product, category, search, **kwargs)

    def _shop_lookup_products(self, attrib_set, options, post, search, website):
        product_count, details, fuzzy_search_term = website._search_with_fuzzy(
            "products_only",
            search,
            limit=None,
            order=self._get_search_order(post),
            options=options,
        )
        search_result = (
            details[0]
            .get("results", request.env["product.template"])
            .with_context(bin_size=True)
        )
        custom_allowed_customer_ids = (
            request.env.user.partner_id.custom_allowed_customer_ids.ids
        )
        custom_allowed_customer_ids.append(request.env.user.partner_id.id)
        custom_allowed_customer_ids.append(False)
        if (
            request.env.user.has_group("base.group_portal")
            and request.env.user.partner_id
        ):
            search_result = search_result.filtered(
                lambda r: r.custom_link_customer.id in custom_allowed_customer_ids or request.env.user.partner_id.id in r.custom_allowed_customer_ids.ids
            )
        # if request.env.user.partner_id.custom_prod_list_id is false, make the search_result empty
        if not request.env.user.partner_id:
            search_result = request.env["product.template"]
        return fuzzy_search_term, product_count, search_result

    @http.route()
    def shop(
        self,
        page=0,
        category=None,
        search="",
        min_price=0.0,
        max_price=0.0,
        ppg=False,
        **post,
    ):
        if not self.check_user_access():
            return request.redirect("/web/login")
        return super().shop(
            page=page,
            category=category,
            search=search,
            min_price=min_price,
            max_price=max_price,
            ppg=ppg,
            **post,
        )

    def check_user_access(self):
        if request.env.user.sudo()._is_public():
            return False
        else:
            return True


class FileDownloadController(http.Controller):

    @http.route("/download/file/<int:attachment_id>", type="http", auth="user")
    def download_file(self, attachment_id):
        attachment = request.env["ir.attachment"].sudo().browse(attachment_id)
        if attachment.exists():
            # Prepare file content for download
            file_content = base64.b64decode(attachment.datas)
            file_name = attachment.name
            # Create the response to trigger the download
            if "." not in file_name:
                # Attempt to guess the file extension from the MIME type
                # extension = mimetypes.guess_extension(attachment.mimetype)
                if attachment.mimetype == "image/tif":
                    file_name += ".tif"
            response = request.make_response(
                file_content,
                headers=[
                    ("Content-Type", attachment.mimetype),
                    ("Content-Disposition", f"attachment; filename={file_name}"),
                ],
            )
            # After the file is served, delete the attachment
            attachment.unlink()
            return response
        else:
            return request.not_found()

    @http.route(
        "/line/update_inputs",
        type="http",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=False,
    )
    def update_line(self, **kw):
        line_id = kw.get("line_id")
        image_file = kw.get("image_file") or False
        tiff_file = kw.get("tiff_file") or False
        tiff_file_name = kw.get("tiff_file_name") or ""
        line_ref = kw.get("line_ref") or ""
        image_img = False
        tiff_img = False
        if image_file:
            image_img = base64.b64encode(image_file.read())
        if tiff_file:
            tiff_img = base64.b64encode(tiff_file.read())
        if line_id:
            try:
                line_obj = request.env["sale.order.line"].sudo().browse(int(line_id))
                if not image_img: 
                    if line_obj.custom_item_image:
                        image_img = line_obj.custom_item_image
                    else:
                        image_img = line_obj.product_id.image_1920
                line_obj.write(
                    {
                        "custom_item_image": image_img, 
                        "custom_tiff_file": tiff_img,
                        "custom_tiff_file_name": tiff_file_name,
                        "custom_order_no": line_ref,
                    }
                )
                return json.dumps({})
            except Exception as e:
                raise UserError("Something went wrong during update sale line")
        return json.dumps({})

    @http.route('/web/content/mo_tiff/<int:mo_id>', type='http', auth="user", website=True)
    def download_tiff(self, mo_id, **kwargs):
        order = request.env['mrp.production'].sudo().browse(mo_id)
        if order.custom_tiff_file:
            tiff_data = base64.b64decode(order.custom_tiff_file)
            tiff_filename = order.name+'.tif'

            response = request.make_response(
                tiff_data,
                headers=[
                    ('Content-Type', 'image/tif'),
                    ('Content-Disposition', f'attachment; filename="{tiff_filename}"')
                ]
            )
            return response
        return request.not_found()

    @http.route(['/custom/image/sale_order_line/<int:line_id>'], type='http', auth="public", website=True)
    def get_sale_order_line_image(self, line_id, **kwargs):
        line = request.env['sale.order.line'].sudo().browse(line_id)
        if not line.exists() or not line.custom_item_image:
            return request.not_found()
        image_data = line.custom_item_image
        image_bytes = base64.b64decode(image_data)
        return http.send_file(
            io.BytesIO(image_bytes),
            filename='image.png',
            mimetype='image/png',
            as_attachment=False
        )
class CustomCustomerPortal(CustomerPortal):
    def _prepare_orders_domain(self, partner):
        return [
            ('message_partner_ids', 'child_of', [partner.commercial_partner_id.id]),
            ('state', 'in', ['sale','cancel']),
        ]

class CustomWebsitePartialPayment(WebsitePartialPayment):
    
    @http.route(['/check_partial_amount'], type="json", auth="public", website=True)
    def check_partial_amount(self, amount):
        res = super().check_partial_amount(amount)
        partner_id = request.env.user.partner_id
        if partner_id.property_payment_term_id.id != request.env.ref("account.account_payment_term_immediate").id:
            values = {}
            values.update({'warning': False, 'adv_payment_amount': 0})
            return json.dumps(values)
        return res

class PaymentPortalPartial(payment_portal.PaymentPortal):
    def _create_transaction(
        self, provider_id, payment_method_id, token_id, amount, currency_id, partner_id, flow,
        tokenization_requested, landing_route, reference_prefix=None, is_validation=False,
        custom_create_values=None, **kwargs
    ):
        tx_sudo = super()._create_transaction(provider_id,payment_method_id, token_id, amount, currency_id, partner_id, flow,
        tokenization_requested, landing_route, reference_prefix, is_validation, custom_create_values,**kwargs)
        # custom code
        order_obj = request.env['sale.order'].sudo()
        if kwargs and kwargs.get('sale_order_id'):
            order_obj = order_obj.browse(kwargs.get('sale_order_id'))  
        if order_obj:
            amount_total = order_obj.amount_total or 0
            payment_amount = amount
            if amount_total != payment_amount and tx_sudo and order_obj.state in ('draft','sent'):
                order_obj.custom_action_confirm()
        return tx_sudo