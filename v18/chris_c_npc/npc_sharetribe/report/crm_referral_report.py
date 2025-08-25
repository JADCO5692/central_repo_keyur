# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CRMReferralReport(models.Model):
    _name = "crm.referral.report"
    _description = "CRM Referral Report"
    _auto = False

    lead_id = fields.Many2one("crm.lead", string="Lead")
    partner_id = fields.Many2one("res.partner", string="NP Name")
    email_from = fields.Char(string="Email")
    reg_date = fields.Char(string="Registration Date")
    stage_id = fields.Many2one("crm.stage", string="Stage")
    custom_user_referral = fields.Char(string="User Referral")
    date = fields.Date(string="Invoice Due Date")
    payment_date = fields.Date(string="First Payment Date")
    invoice_amount = fields.Float(string="Invoice Amount")
    invoice_id = fields.Many2one("account.move", string="Invoice")

    def init(self):
        self.env.cr.execute("DROP VIEW IF EXISTS crm_referral_report")
        self.env.cr.execute(
            """
            CREATE OR REPLACE VIEW crm_referral_report AS (
                SELECT
                    ROW_NUMBER() OVER() as id,
                    l.id as lead_id,
                    l.partner_id as partner_id,
                    l.email_from,
                    l.phone,
                    l.custom_user_referral,
                    l.reg_date,
                    l.stage_id,
                    am.invoice_date_due as date,
                    am.amount_total as invoice_amount,
                    payments.first_payment_date as payment_date,
                    am.id as invoice_id
                FROM crm_lead l
                LEFT JOIN account_move am ON am.partner_id = l.partner_id
                LEFT JOIN (
                    SELECT 
                        aml_invoice.move_id,
                        MIN(aml_payment.date) as first_payment_date
                    FROM account_move_line aml_invoice
                    INNER JOIN account_partial_reconcile apr ON (
                        apr.debit_move_id = aml_invoice.id OR apr.credit_move_id = aml_invoice.id
                    )
                    INNER JOIN account_move_line aml_payment ON (
                        CASE 
                            WHEN apr.debit_move_id = aml_invoice.id THEN apr.credit_move_id = aml_payment.id
                            ELSE apr.debit_move_id = aml_payment.id
                        END
                    )
                    INNER JOIN account_move am_payment ON am_payment.id = aml_payment.move_id
                    WHERE aml_invoice.account_id IN (
                        SELECT id FROM account_account WHERE account_type = 'asset_receivable'
                    )
                    AND am_payment.move_type IN ('entry', 'in_receipt')
                    GROUP BY aml_invoice.move_id
                ) payments ON payments.move_id = am.id
                WHERE l.custom_user_referral IS NOT NULL
                    AND am.move_type = 'out_invoice'
                    AND am.state = 'posted'
            )
        """
        )
