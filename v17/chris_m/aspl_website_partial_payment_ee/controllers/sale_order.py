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
from odoo.http import request


class SaleOrderPartialPayment(http.Controller):

    @http.route(['/sale_order/partial_pay/price'], type="json", auth="public", website=True)
    def add_partial_amount_sale_partial(self, amount, sale_order):
        amount = float(amount)
        sale_order_id = request.env['sale.order'].browse(int(sale_order))
        sale_order_id.sudo().write({'partial_pay_amount': amount})

    @http.route(['/check_sale_order_partial_payment'], type="json", auth="public", website=True)
    def check_partial_payment_order(self, **kw):
        values = {}
        sale_ids = request.env['sale.order'].sudo().search([('partner_id', '=', request.env.user.partner_id.id)])
        partner_id = request.env.user.partner_id
        from_website_max_partial_order = float(request.env['ir.config_parameter'].sudo()
                                               .get_param('aspl_website_partial_payment_ee.max_partial_order'))
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

    @http.route(['/check_sale_order_partial_amount'], type="json", auth="public", website=True)
    def check_partial_amount(self, amount, sale_order):
        values = {}
        order = request.env['sale.order'].browse(int(sale_order))
        partner_id = request.env.user.partner_id
        from_website_adv_payment_amount = float(request.env['ir.config_parameter'].sudo()
                                                .get_param('aspl_website_partial_payment_ee.adv_payment_amount'))
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

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
