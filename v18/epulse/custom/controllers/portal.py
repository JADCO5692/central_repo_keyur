from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo import http
from odoo.http import request
class CustomCustomerPortal(CustomerPortal):
    @http.route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        print("request session in my homee is",list(request.session.keys()))
        # valid__user = request.session.get('valid_user')
        print("In home override")
        base_url = request.httprequest.url_root.rstrip('/')
        if request.session.get('valid_account_user'):
            return super(CustomCustomerPortal, self).home(**kw)
        if request.session.get('valid_user') and request.session.get('bulk'):
            return super(CustomCustomerPortal, self).home(**kw)
        else:
            return request.redirect(f"{base_url}/check-account-pin")
        # http.request.session.update({'website_sale_cart_quantity': 0})
        # request.session['dropship'] = request.session.get('dropship', False)
        # print("The res qcontext isss", res.qcontext)
        # print("&&&&&&&&&&", request.session.get('dropship', False))

        # return res

