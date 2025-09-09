# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models


class AccountReportExtended(models.Model):
    _inherit = "account.report"

    def _get_options(self, previous_options=None):
        # OVERRIDE
        options = super(AccountReportExtended, self)._get_options(previous_options)

        # If manual values were stored in the context, we store them as options.
        # This is useful for report printing, were relying only on the context is
        # not enough, because of the use of a route to download the report (causing
        # a context loss, but keeping the options).

        if self._context.get('shopify_report'):
            shopify_instance_ids = self.env['shopify.instance.ept'].search([('active', '=', 'True')])

            if shopify_instance_ids:
                options.update(
                    {'analytic_accounts_groupby': shopify_instance_ids.mapped('shopify_analytic_account_id').ids})
        return options
