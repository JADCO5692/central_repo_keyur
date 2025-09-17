from odoo import http
from odoo.http import request
from odoo.tools.translate import _
from odoo.addons.website_sale.controllers.main import WebsiteSale
import json
import logging

logger = logging.getLogger(__name__)


class WebsiteSaleCustom(WebsiteSale):
        def _prepare_checkout_page_values(self, order_sudo, **_kwargs):
            PartnerSudo = order_sudo.partner_id.with_context(show_address=1)
            commercial_partner_sudo = order_sudo.partner_id.commercial_partner_id

            billing_partners_sudo = PartnerSudo.search([
                ('id', 'child_of', commercial_partner_sudo.ids),
                '|',
                ('type', 'in', ['invoice', 'other']),
                ('id', '=', commercial_partner_sudo.id),
            ], order='id desc') | order_sudo.partner_id

            delivery_partners_sudo = PartnerSudo.search([
                ('id', 'child_of', commercial_partner_sudo.ids),
                '|',
                ('type', 'in', ['delivery', 'other']),
                ('id', '=', commercial_partner_sudo.id),
            ], order='id desc') | order_sudo.partner_id

            if order_sudo.partner_id != commercial_partner_sudo:
                if not self._check_billing_address(commercial_partner_sudo):
                    billing_partners_sudo = billing_partners_sudo.filtered(
                        lambda p: p.id != commercial_partner_sudo.id
                    )
                if not self._check_delivery_address(commercial_partner_sudo):
                    delivery_partners_sudo = delivery_partners_sudo.filtered(
                        lambda p: p.id != commercial_partner_sudo.id
                    )

            # 💡 Custom filter: if 'bulk' session flag is set, exclude dropship addresses with so_id
            if request.session.get('bulk'):
                print("in bulk condiiton")
                delivery_partners_sudo = delivery_partners_sudo.filtered(
                    lambda p: not (getattr(p, 'order_type', '') == 'dropship' and getattr(p, 'so_id', False))
                )

            return {
                'order': order_sudo,
                'website_sale_order': order_sudo,
                'billing_addresses': billing_partners_sudo,
                'delivery_addresses': delivery_partners_sudo,
                'use_delivery_as_billing': (
                        order_sudo.partner_shipping_id == order_sudo.partner_invoice_id
                ),
                'only_services': order_sudo.only_services,
                'json_pickup_location_data': json.dumps(order_sudo.pickup_location_data or {}),
            }

        @http.route(['/shop/checkout'], type='http', auth="public", website=True)
        def shop_checkout(self, try_skip_step=None, **query_params):
            """
            Override the checkout route to redirect to /shop/address if dropship is in session
            and the delivery address is not yet set. Applies when accessing /shop/checkout?try_skip_step=true.
            """
            logger.info("Checkout route accessed. Session: %s, Query params: %s", request.session,
                    request.httprequest.args)

            parent_class = super(WebsiteSaleCustom, self).__thisclass__.__mro__[1].__name__
            logger.info("Parent class of WebsiteSaleCustom: %s", parent_class)

            if request.session.get('dropship') and not query_params.get('dropship_address_submitted', False):
                order_sudo = request.website.sale_get_order()
                logger.info("Dropship detected. Order partner_shipping_id: %s", order_sudo.partner_shipping_id)
                logger.info("No delivery address set, redirecting to /shop/address")
                checkout_url='/shop/checkout?dropship_address_submitted=True'
                redirect_url="/shop/address?address_type=delivery&callback=%s"%(checkout_url)
                return request.redirect(redirect_url)
            if request.session.get('dropship_address_submitted'):
                request.session.pop('dropship_address_submitted')
            return super(WebsiteSaleCustom, self).shop_checkout()

        @http.route([
            '/shop',
            '/shop/page/<int:page>',
            '/shop/category/<model("product.public.category"):category>',
            '/shop/category/<model("product.public.category"):category>/page/<int:page>',
        ], type='http', auth="public", website=True, sitemap='sitemap_shop')
        def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, ppg=False, **post):
            res = super(WebsiteSaleCustom, self).shop(
                page=page,
                category=category,
                search=search,
                min_price=min_price,
                max_price=max_price,
                ppg=ppg,
                **post
            )
            valid_user = request.session.get('valid_user')
            if not valid_user:
                base_url = request.httprequest.url_root.rstrip('/')
                return request.redirect(f"{base_url}/check-pin")
            http.request.session.update({'website_sale_cart_quantity': 0})
            request.session['dropship'] = request.session.get('dropship', False)
            return res

        def _cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
            """Override to ensure session info is updated before cart operations."""
            request.session['dropship'] = request.session.get('dropship', False)
            return super(WebsiteSaleCustom, self)._cart_update(product_id, add_qty=add_qty, set_qty=set_qty, **kw)

        @http.route('/website/session/info', type='json', auth="public", website=True)
        def website_session_info(self):
            """Override to add custom session data."""
            session_info = super(WebsiteSaleCustom, self).website_session_info()
            session_info['dropship'] = request.session.get('dropship', False)
            return session_info
