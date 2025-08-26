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

from odoo.http import request
from odoo import _
from odoo.exceptions import AccessError, ValidationError, UserError
from odoo.fields import Command
from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing
from odoo.addons.payment.controllers import portal as payment_portal


class PaymentPortalPartial(payment_portal.PaymentPortal):

    # V17
    def _create_transaction(
        self, provider_id, payment_method_id, token_id, amount, currency_id, partner_id, flow,
        tokenization_requested, landing_route, reference_prefix=None, is_validation=False,
        custom_create_values=None, **kwargs
    ):
        """ Create a draft transaction based on the payment context and return it.

        :param int provider_id: The provider of the provider payment method or token, as a
                                `payment.provider` id.
        :param int|None payment_method_id: The payment method, if any, as a `payment.method` id.
        :param int|None token_id: The token, if any, as a `payment.token` id.
        :param float|None amount: The amount to pay, or `None` if in a validation operation.
        :param int|None currency_id: The currency of the amount, as a `res.currency` id, or `None`
                                     if in a validation operation.
        :param int partner_id: The partner making the payment, as a `res.partner` id.
        :param str flow: The online payment flow of the transaction: 'redirect', 'direct' or 'token'.
        :param bool tokenization_requested: Whether the user requested that a token is created.
        :param str landing_route: The route the user is redirected to after the transaction.
        :param str reference_prefix: The custom prefix to compute the full reference.
        :param bool is_validation: Whether the operation is a validation.
        :param dict custom_create_values: Additional create values overwriting the default ones.
        :param dict kwargs: Locally unused data passed to `_is_tokenization_required` and
                            `_compute_reference`.
        :return: The sudoed transaction that was created.
        :rtype: payment.transaction
        :raise UserError: If the flow is invalid.
        """
        # Prepare create values
        if flow in ['redirect', 'direct']:  # Direct payment or payment with redirection
            provider_sudo = request.env['payment.provider'].sudo().browse(provider_id)
            token_id = None
            tokenize = bool(
                # Don't tokenize if the user tried to force it through the browser's developer tools
                provider_sudo.allow_tokenization
                # Token is only created if required by the flow or requested by the user
                and (provider_sudo._is_tokenization_required(**kwargs) or tokenization_requested)
            )
        elif flow == 'token':  # Payment by token
            token_sudo = request.env['payment.token'].sudo().browse(token_id)

            # Prevent from paying with a token that doesn't belong to the current partner (either
            # the current user's partner if logged in, or the partner on behalf of whom the payment
            # is being made).
            partner_sudo = request.env['res.partner'].sudo().browse(partner_id)
            if partner_sudo.commercial_partner_id != token_sudo.partner_id.commercial_partner_id:
                raise AccessError(_("You do not have access to this payment token."))

            provider_sudo = token_sudo.provider_id
            payment_method_id = token_sudo.payment_method_id.id
            tokenize = False
        else:
            raise ValidationError(
                _("The payment should either be direct, with redirection, or made by a token.")
            )

        reference = request.env['payment.transaction']._compute_reference(
            provider_sudo.code,
            prefix=reference_prefix,
            **(custom_create_values or {}),
            **kwargs
        )
        if is_validation:  # Providers determine the amount and currency in validation operations
            amount = provider_sudo._get_validation_amount()
            payment_method = request.env['payment.method'].browse(payment_method_id)
            currency_id = provider_sudo.with_context(
                validation_pm=payment_method  # Will be converted to a kwarg in master.
            )._get_validation_currency().id

        # custom code
        if kwargs and kwargs.get('sale_order_id'):
            order_id = request.env['sale.order'].browse(kwargs.get('sale_order_id'))
            if order_id.partial_pay_amount > 0.0:
                amount = order_id.partial_pay_amount

        if custom_create_values and custom_create_values.get('invoice_ids') and custom_create_values.get('invoice_ids')[0] and custom_create_values.get('invoice_ids')[0][2]:
            invoice_id = request.env['account.move'].browse(custom_create_values.get('invoice_ids')[0][2])
            if invoice_id and invoice_id.partial_pay > 0.0:
                amount = invoice_id.partial_pay
        # complete custom code

        # Create the transaction
        tx_sudo = request.env['payment.transaction'].sudo().create({
            'provider_id': provider_sudo.id,
            'payment_method_id': payment_method_id,
            'reference': reference,
            'amount': amount,
            'currency_id': currency_id,
            'partner_id': partner_id,
            'token_id': token_id,
            'operation': f'online_{flow}' if not is_validation else 'validation',
            'tokenize': tokenize,
            'landing_route': landing_route,
            **(custom_create_values or {}),
        })  # In sudo mode to allow writing on callback fields

        if flow == 'token':
            tx_sudo._send_payment_request()  # Payments by token process transactions immediately
        else:
            tx_sudo._log_sent_message()

        # Monitor the transaction to make it available in the portal.
        PaymentPostProcessing.monitor_transaction(tx_sudo)

        return tx_sudo

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:       