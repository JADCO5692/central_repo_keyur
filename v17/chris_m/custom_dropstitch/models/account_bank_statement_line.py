from odoo import models, fields, api

class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    account_id = fields.Many2one(
        'account.account',
        string='Account',
        help='Account related to this bank statement line.'
    )

    @api.onchange('partner_id')
    def _onchange_partner_update_expense_account(self):
        if self.partner_id:
            # Assuming the partner has a default expense account
            self.account_id = self.partner_id.custom_property_expense_account_id
        else:
            self.account_id = False

    def _prepare_move_line_default_vals(self, counterpart_account_id=None):
        if self.account_id:
            counterpart_account_id = self.account_id.id
        return super()._prepare_move_line_default_vals(counterpart_account_id)
