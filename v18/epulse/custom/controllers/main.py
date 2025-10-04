from odoo import http, fields
from odoo.tools.translate import _
from odoo.exceptions import UserError
import logging
from odoo.http import request, route
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


class CustomCheckoutController(http.Controller):
    @http.route('/custom/custom_checkout', type='json', auth='public', methods=['POST'])
    def custom_checkout(self, **kwargs):
        sale_order_id = request.session.get('sale_order_id')
        if not sale_order_id:
            raise UserError("No sale order found in session.")

        sale_order = request.env['sale.order'].sudo().browse(sale_order_id)

        cargo_location = kwargs.get("cargo_location")
        cargo_instructions = kwargs.get("cargo_instructions")
        print("Cargo Location:", cargo_location)
        if cargo_location or cargo_instructions:
            sale_order.write({
                "cargo_location": cargo_location,
                "cargo_instructions": cargo_instructions,
            })

        bulk_bool = request.session.get('bulk')
        dropship_bool = request.session.get('dropship')
        order_type = 'bulk'
        if dropship_bool:
            order_type = 'dropship'
        
        portal_url = sale_order.action_custom_checkout(order_type)
        if request.session.get('dropship'):
            company = request.env.company
            template = company.mail_template_id
            email_values = {'email_to': sale_order.partner_shipping_id.email, 'email_from': company.email}
            if template and sale_order.partner_shipping_id.email:
                template.sudo().send_mail(sale_order.id,email_values=email_values ,force_send=True)
            so_template = sale_order._find_mail_template()
            base_url = request.httprequest.url_root.rstrip('/')
            # sale_order._send_order_notification_mail(so_template)
            portal_url = f"{base_url}/thankyou"
        return {'redirect_url': portal_url}

    @http.route('/thankyou', type='http', auth='public', website=True, methods=['GET','POST'], csrf=False)
    def thankyou_page(self, **post):
            return request.render('custom.thankyou_page_template')

    @http.route('/pin_page', type='http', auth='public', website=True)
    def pin_page(self, **kwargs):
        return request.render('custom.validate_pin_template', {})

    @http.route('/check-pin', type='http', auth='public', website=True, methods=['GET','POST'], csrf=False)
    def check_pin(self, **post):
        if request.httprequest.method == 'GET':
            return request.render('custom.validate_pin_template', {'dropship': request.session.get('dropship', False),
                                                                   'from_portal': False,})
        elif request.httprequest.method == 'POST':
            entered_pin = post.get('pin')
            users=request.env['res.users'].browse(request.session.get('uid'))

            correct_pin = users.partner_id.user_pwd
            base_url = request.httprequest.url_root.rstrip('/')
            order_type = post.get('order_type')
            #emptying the sol before deleting the sale order
            if order_type == 'dropship':
                request.session['dropship'] = True
                #clear bulk
                request.session['bulk'] = False
                request.session['sale_order_id'] = False
                request.session['valid_user'] = True
                return request.redirect(f"{base_url}/shop")
            elif order_type == 'bulk':
                #clear dropship
                request.session['dropship'] = False
                request.session['bulk'] = True
                request.session['sale_order_id'] = False
            if entered_pin == correct_pin and request.session.get('bulk'):
                request.session['valid_user'] = True
                return request.redirect(f"{base_url}/shop")
            else:
                error_message = "Invalid PIN, please try again."
                return request.render('custom.validate_pin_template', {'error_message': error_message,
                                                                       'from_portal': False,})

    @http.route('/check-account-pin', type='http', auth='public', website=True, methods=['GET', 'POST'], csrf=False)
    def check_account_pin(self, **post):
        base_url = request.httprequest.url_root.rstrip('/')
        if request.httprequest.method == 'GET':
            if request.session.get('valid_user') and request.session.get('bulk'):
                return request.redirect(f"{base_url}/my/home")
            return request.render('custom.validate_pin_template_account', {'dropship': request.session.get('dropship', False),
                                                                   'from_portal': False, })
        elif request.httprequest.method == 'POST':
            print("in post methoodddd1111")
            entered_pin = post.get('account_pin')
            users = request.env['res.users'].browse(request.session.get('uid'))

            correct_pin = users.partner_id.user_pwd
            if entered_pin == correct_pin:
                print("In if condition to redirect to my home")
                request.session['valid_account_user'] = True
                return request.redirect(f"{base_url}/my/home")
            else:
                error_message = "Invalid PIN, please try again."
                return request.render('custom.validate_pin_template_account', {'error_message': error_message,
                                                                       'from_portal': False, })
