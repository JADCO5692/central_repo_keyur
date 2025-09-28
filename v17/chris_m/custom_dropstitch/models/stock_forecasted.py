# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class StockForecasted(models.AbstractModel):
    _inherit = 'stock.forecasted_product_product'

    def _prepare_report_line(self, quantity, move_out=None, move_in=None,
                         replenishment_filled=True, product=False,
                         reserved_move=False, in_transit=False, read=True):
        res = super()._prepare_report_line(quantity, move_out, move_in,
                                        replenishment_filled, product,
                                        reserved_move, in_transit, read)

        if res.get('document_in') and res['document_in'].get('_name'):
            model = res['document_in']['_name']
            rec = self.env[model].sudo().browse(res['document_in']['id'])
            field = self.env['ir.model.fields'].sudo().search([
                ('model_id.model', '=', model),
                ('name', '=', 'state')
            ], limit=1)
            if field:
                state_field = field.selection_ids.filtered(lambda a: a.value == rec.state)
                res['document_in']['state'] = state_field[:1].name if state_field else rec.state

        if res.get('reservation') and res['reservation'].get('_name'):
            model = res['reservation']['_name']
            rec = self.env[model].sudo().browse(res['reservation']['id'])
            field = self.env['ir.model.fields'].sudo().search([
                ('model_id.model', '=', model),
                ('name', '=', 'state')
            ], limit=1)
            if field:
                state_field = field.selection_ids.filtered(lambda a: a.value == rec.state)
                res['reservation']['state'] = state_field[:1].name if state_field else rec.state

        return res
