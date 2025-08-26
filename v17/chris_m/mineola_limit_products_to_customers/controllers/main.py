# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.osv import expression
from werkzeug.exceptions import NotFound


class WebsiteSaleInherit(WebsiteSale):
    def _get_search_domain(self, *args, **kwargs):
        super_domain = super(WebsiteSaleInherit, self)._get_search_domain(
            *args, **kwargs
        )
        if request.env.user.has_group('base.group_portal') and request.env.user.partner_id.custom_prod_list_id:
            domain = [
                ("id", "in", request.env.user.partner_id.custom_prod_list_id.product_tmpl_ids.ids),
                ('is_published', '=', True),
                ('sale_ok', '=', True)
            ]
            return expression.AND([domain, super_domain])
        else:
            return super_domain

    @http.route(['/shop/<model("product.template"):product>'], type='http', auth="public", website=True, sitemap=True)
    def product(self, product, category='', search='', **kwargs):
        if request.env.user.has_group('base.group_portal') and \
                request.env.user.partner_id.custom_prod_list_id and \
                product.id not in request.env.user.partner_id.custom_prod_list_id.product_tmpl_ids.ids:
            raise NotFound()
        return super().product(product, category, search, **kwargs)

    def _shop_lookup_products(self, attrib_set, options, post, search, website):
        product_count, details, fuzzy_search_term = website._search_with_fuzzy("products_only", search,
                                                                               limit=None,
                                                                               order=self._get_search_order(post),
                                                                               options=options)
        search_result = details[0].get('results', request.env['product.template']).with_context(bin_size=True)
        if request.env.user.has_group('base.group_portal') and request.env.user.partner_id.custom_prod_list_id:
            search_result = search_result.filtered(lambda r: r.id in request.env.user.partner_id.custom_prod_list_id.product_tmpl_ids.ids)
        # if request.env.user.partner_id.custom_prod_list_id is false, make the search_result empty
        if not request.env.user.partner_id.custom_prod_list_id:
            search_result = request.env['product.template']
        return fuzzy_search_term, product_count, search_result
    