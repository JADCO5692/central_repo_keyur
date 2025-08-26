from odoo.fields import Command
import binascii
from odoo import fields, http, _
from odoo import http
from odoo.http import request
from odoo.exceptions import UserError
from odoo.addons.sale.controllers import portal 
from odoo.addons.payment.controllers import portal as payment_portal 
from odoo.addons.portal.controllers.portal import pager as portal_pager

class PortalBits(portal.CustomerPortal):
    # compute payment amount
    @http.route("/compute/payable_amount", type="json", auth="public")
    def get_dashboard_data(self, order_ids, **kw):
        orders_sudo = request.env['sale.order'].sudo().browse(order_ids) 
        sale_amount_total = 0.0 
        currency_symbol = request.env.user.currency_id.symbol
        for order in orders_sudo: 
            sale_amount_total += order.amount_total
        return {'total_amount': int(sale_amount_total),'currency':currency_symbol}
    
    # call for write sign data
    @http.route(['/my/orders_sign/accept'], type='json', auth="public", website=True)
    def portal_orders_accept(self, order_ids=[], name=None, signature=None):
        access_token = request.httprequest.args.get('access_token')
        if not order_ids: 
            return {'error': _('Invalid order data.')}
        
        order_sudo = request.env['sale.order'].sudo().browse(order_ids)
        downpayment = 'true' if self.is_get_down_payment(order_sudo) else 'false'
        try:
            for order in order_sudo:
                if order.require_signature:
                    order.write({
                        'signed_by': name,
                        'signed_on': fields.Datetime.now(),
                        'signature': signature,
                    })
                request.env.cr.commit()
        except (TypeError, binascii.Error) as e:
            return {'error': _('Invalid signature data.')}
        oids = ','.join(str(id) for id in order_ids)
        return { 
            'force_refresh': True,
            'redirect_url': '/my/quotes?csrf_token='+access_token+'&downpayment='+downpayment+'&message=sign_ok&allow_payment=yes&oid='+oids,
        } 

    # call direct when no any sign order selected
    @http.route(['/accept/payment'], type='json', auth="public", website=True)
    def accept_payment(self, order_ids=[]):
        access_token = request.csrf_token()
        if not order_ids: 
            return {'error': _('Invalid order data.')}
        
        order_sudo = request.env['sale.order'].sudo().browse(order_ids)
        downpayment = 'true' if self.is_get_down_payment(order_sudo) else 'false'
         
        oids = ','.join(str(id) for id in order_ids)
        return { 
            'force_refresh': True,
            'redirect_url': '/my/quotes?csrf_token='+access_token+'&downpayment='+downpayment+'&message=sign_ok&allow_payment=yes&oid='+oids,
        } 

    @http.route(['/my/quotes', '/my/quotes/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_quotes(self, **kwargs):
        values = self._prepare_sale_portal_rendering_values(quotation_page=True, **kwargs)
        request.session['my_quotations_history'] = values['quotations'].ids[:100]
        values['is_loader'] = True
        downpayment = request.httprequest.args.get('downpayment')
        if request.params.get('allow_payment') == 'yes':
            order_ids = list(map(int, request.params.get('oid').split(',')))
            quote_ids = values['quotations'].ids
            if not any(item in quote_ids for item in order_ids):
                return request.redirect('/my')
            order_sudo = request.env['sale.order'].sudo().browse(order_ids)
            values['sale_order_ids'] = order_sudo.ids
            values['sale_order'] = order_sudo[0]
            values.update(self._get_payment_values(order_sudo[0], downpayment = downpayment))
            values.update(self._get_order_values(order_sudo,downpayment)) 
            values['transaction_route'] = '/my/orders/transaction?&oids='+','.join(map(str,order_sudo.ids))
            values['landing_route'] = '/payment/successfull?&oids='+','.join(map(str,order_sudo.ids))

        return request.render("sale.portal_my_quotations", values)
    
    @http.route(['/payment/successfull'], type='http', auth="user", website=True)
    def payment_success(self, **kwargs): 
        order_ids = request.httprequest.args.get('oids')
        order_ids = list(map(int, order_ids.split(',')))
        orders = request.env['sale.order'].sudo().browse(order_ids)
        return request.render('portal_bulk_payment.view_payment_success',{'orders':orders})
    
    def _get_order_values(self,order_sudo,downpayment): 
        amount_vals = {}
        total_amount = 0
        partner = request.env.user.partner_id
        sale_amount_total = 0 
        prepayment_available = False
        for order in order_sudo:
            total_amount += order._get_prepayment_required_amount()
            if not prepayment_available:
                prepayment_available = order.prepayment_percent and order.prepayment_percent != 1.0
            sale_amount_total += order.amount_total 
        amount_vals['prepayment_available'] = prepayment_available 
        amount_vals['prepayment_amount'] = total_amount
        amount_vals['sale_amount_total'] = sale_amount_total
        if downpayment and downpayment == 'true': 
            amount_vals['amount'] = total_amount
        else:
            amount_vals['amount'] = sale_amount_total

        amount_vals['currency_id'] = partner.currency_id
        amount_vals['payment_on_behalf'] = partner.commercial_partner_id.name or partner.name
        return amount_vals

    # check for down payment
    def is_get_down_payment(self,orders_sudo): 
        is_down_payment = False
        for order in orders_sudo:
            if order.require_payment and order.prepayment_percent and order.prepayment_percent != 1.0:
                is_down_payment = True
            else:
                is_down_payment = False
        return is_down_payment

class PaymentPortalBits(payment_portal.PaymentPortal):
    _items_per_page_vk = 1000

    @http.route('/my/orders/transaction', type='json', auth='public')
    def portal_orders_transaction(self, **kwargs): 
        order_ids = request.httprequest.args.get('oids')
        order_ids= list(map(int, order_ids.split(',')))
        try:
            logged_in = not request.env.user._is_public()
            partner_sudo = request.env.user.partner_id
            del kwargs['access_token']
            self._validate_transaction_kwargs(kwargs)
            kwargs.update({
                'partner_id': partner_sudo.id,
                'currency_id': partner_sudo.currency_id.id,
                'sale_order_id': False,  # Include the SO to allow Subscriptions tokenizing the tx
            })
            tx_sudo = self._create_transaction(
                custom_create_values={'sale_order_ids': [Command.set(order_ids)]}, **kwargs,
            )
        except Exception:
            raise UserError(_("Error Occured in transaction"))
        return tx_sudo._get_processing_values() 
    
    # replaced and changes 
    def _prepare_sale_portal_rendering_values(
        self, page=1, date_begin=None, date_end=None, sortby=None, quotation_page=False, **kwargs
    ):
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

        pager_values = portal_pager(
            url=url,
            total=SaleOrder.search_count(domain),
            page=page,
            step=self._items_per_page_vk,
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
        )
        orders = SaleOrder.search(domain, order=sort_order, limit=self._items_per_page_vk, offset=pager_values['offset'])

        values.update({
            'date': date_begin,
            'quotations': orders.sudo() if quotation_page else SaleOrder,
            'orders': orders.sudo() if not quotation_page else SaleOrder,
            'page_name': 'quote' if quotation_page else 'order',
            'pager': pager_values,
            'default_url': url,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
        })

        return values
    
    