 
from odoo.http import request
  
from odoo.addons.portal.controllers.portal import pager as portal_pager

from odoo.addons.sale.controllers.portal import CustomerPortal


class CustomerPortalNPC(CustomerPortal):
    def _prepare_orders_domain(self, partner):
        # return super()._prepare_orders_domain(partner)
        return [
            ('partner_id', 'in', request.env.user.partner_id.ids),
            ('state', '=', 'sale'),
        ]
    
    def _prepare_sale_portal_rendering_values(self, page=1, date_begin=None, date_end=None, sortby=None, quotation_page=False, **kwargs):
        SaleOrder = request.env['sale.order']

        if not sortby:
            sortby = 'date'

        partner = request.env.user.partner_id
        values = self._prepare_portal_layout_values()

        if quotation_page:
            url = "/my/quotes"
            domain = self._prepare_quotations_domain(partner)
        else:
            url = "/my/orders"
            domain = self._prepare_orders_domain(partner)

        searchbar_sortings = self._get_sale_searchbar_sortings()

        sort_order = searchbar_sortings[sortby]['order']

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        url_args = {'date_begin': date_begin, 'date_end': date_end}

        if len(searchbar_sortings) > 1:
            url_args['sortby'] = sortby

        pager_values = portal_pager(
            url=url,
            total=SaleOrder.sudo().search_count(domain),
            page=page,
            step=self._items_per_page,
            url_args=url_args,
        )
        orders = SaleOrder.sudo().search(domain, order=sort_order, limit=self._items_per_page, offset=pager_values['offset'])

        values.update({
            'date': date_begin,
            'quotations': orders.sudo() if quotation_page else SaleOrder,
            'orders': orders.sudo() if not quotation_page else SaleOrder,
            'page_name': 'quote' if quotation_page else 'order',
            'pager': pager_values,
            'default_url': url,
        })

        if len(searchbar_sortings) > 1:
            values.update({
                'sortby': sortby,
                'searchbar_sortings': searchbar_sortings,
            })

        return values