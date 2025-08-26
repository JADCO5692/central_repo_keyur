# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

import json

from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsitePartialPayment(http.Controller):

    @http.route(['/sale/partial_pay/price'], type="json", auth="public", website=True)
    def add_partial_amount(self, amount):
        amount = float(amount)
        order = request.website.sale_get_order()
        order.partial_pay_amount = amount

    @http.route(['/check_partial_payment_minimum_payment_term'], type="json", auth="public", website=True)
    def check_partial_payment_minimum_payment_term(self, **kw):
        values = {}
        partner_id = request.env.user.partner_id
        invoice_id = request.env['account.move'].sudo().browse(int(kw.get('invoice_id')))
        from_website_min_payment_term = float(request.env['ir.config_parameter'].sudo().get_param(
            'aspl_website_partial_payment_ee.min_payment_term'))
        if partner_id and partner_id.min_payment_term:
            min_payment_term = partner_id.min_payment_term
        else:
            min_payment_term = from_website_min_payment_term
        move_line_list = []
        for partial, amount, counterpart_line in invoice_id._get_reconciled_invoices_partials()[0]:
            move_line_list.append(counterpart_line.id)
        payment_ids = request.env['account.move.line'].sudo().search([('id', 'in', move_line_list)])

        if (int(min_payment_term) - len(payment_ids)) == 1 and float(kw.get('amount')) < float(invoice_id.amount_residual):
            values.update({'warning': True})
        else:
            values.update({'warning': False})
        return json.dumps(values)

    @http.route(['/check_partial_payment_order'], type="json", auth="public", website=True)
    def check_partial_payment_order(self, **kw):
        values = {}
        sale_ids = request.env['sale.order'].sudo().search([('partner_id', '=', request.env.user.partner_id.id)])
        partner_id = request.env.user.partner_id
        from_website_max_partial_order = float(request.env['ir.config_parameter'].sudo().get_param(
            'aspl_website_partial_payment_ee.max_partial_order'))
        if partner_id and partner_id.max_partial_order:
            max_partial_order = partner_id.max_partial_order
        else:
            max_partial_order = from_website_max_partial_order
        count = 0
        for each in sale_ids:
            invoice_ids = each.invoice_ids.filtered(
                lambda l: l.state == 'posted' and l.payment_state == 'partial' and l.amount_residual > 0)
            count += len(invoice_ids)
        if float(max_partial_order) > float(count):
            values.update({'warning': False, 'max_partial_order': max_partial_order})
        else:
            values.update({'warning': True, 'max_partial_order': max_partial_order})
        return json.dumps(values)

    @http.route(['/check_partial_amount'], type="json", auth="public", website=True)
    def check_partial_amount(self, amount):
        values = {}
        order = request.website.sale_get_order()
        partner_id = request.env.user.partner_id
        from_website_adv_payment_amount = float(request.env['ir.config_parameter'].sudo().get_param(
            'aspl_website_partial_payment_ee.adv_payment_amount'))
        if partner_id and partner_id.adv_payment_amount:
            adv_payment_amount = partner_id.adv_payment_amount
        else:
            adv_payment_amount = from_website_adv_payment_amount
        need_to_pay_amount = (order.amount_total * adv_payment_amount) / 100
        if need_to_pay_amount and float(need_to_pay_amount) > float(amount):
            values.update({'warning': True, 'adv_payment_amount': adv_payment_amount})
        else:
            values.update({'warning': False, 'adv_payment_amount': adv_payment_amount})
        return json.dumps(values)

    @http.route(['/invoice/partial_pay/price'], type="json", auth="public", website=True)
    def add_partial_invoice_amount(self, amount, invoice):
        invoice_id = request.env['account.move'].browse(int(invoice))
        if amount:
            amount = float(amount)
            if invoice_id:
                invoice_id.partial_pay = amount

    @http.route('/check_partial_payment_configuration', type='http', auth="public", website=True, csrf=False)
    def check_partial_payment_configuration(self, **kw):
        values = {}
        partner_id = request.env.user.partner_id
        from_website_min_order_amount = float(request.env['ir.config_parameter'].sudo()
                                              .get_param('aspl_website_partial_payment_ee.min_order_amount'))
        if partner_id and partner_id.min_order_amount:
            min_order_amount = partner_id.min_order_amount
        else:
            min_order_amount = from_website_min_order_amount
        if kw.get('amount') and float(kw.get('amount').replace(",", "")) >= float(min_order_amount):
            values.update({'hide': False})
        else:
            values.update({'hide': True})
        return json.dumps(values)


class WebsiteSalePartial(WebsiteSale):

    @http.route(['/shop/payment'], type='http', auth="public", website=True)
    def shop_payment(self, **post):
        res = super(WebsiteSalePartial, self).shop_payment(**post)
        res.qcontext['page_name'] = 'payment'
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
