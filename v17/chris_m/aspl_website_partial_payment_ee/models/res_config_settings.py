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

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    min_order_amount = fields.Float(
        string="Minimum Order Amount", required=True
    )
    adv_payment_amount = fields.Integer(
        string="Advance Payment Amount(%)", required=True
    )
    min_payment_term = fields.Integer(
        string="Minimum Payment Term", required=True
    )
    max_partial_order = fields.Integer(
        string="Maximum Partial Payment", required=True
    )

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            min_order_amount=float(
                self.env["ir.config_parameter"]
                .sudo()
                .get_param(
                    "aspl_website_partial_payment_ee.min_order_amount"
                )
            ),
            adv_payment_amount=int(
                self.env["ir.config_parameter"]
                .sudo()
                .get_param(
                    "aspl_website_partial_payment_ee.adv_payment_amount"
                )
            ),
            min_payment_term=int(
                self.env["ir.config_parameter"]
                .sudo()
                .get_param(
                    "aspl_website_partial_payment_ee.min_payment_term"
                )
            ),
            max_partial_order=int(
                self.env["ir.config_parameter"]
                .sudo()
                .get_param(
                    "aspl_website_partial_payment_ee.max_partial_order"
                )
            ),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            "aspl_website_partial_payment_ee.min_order_amount",
            self.min_order_amount,
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "aspl_website_partial_payment_ee.adv_payment_amount",
            self.adv_payment_amount,
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "aspl_website_partial_payment_ee.min_payment_term",
            self.min_payment_term,
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "aspl_website_partial_payment_ee.max_partial_order",
            self.max_partial_order,
        )


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
