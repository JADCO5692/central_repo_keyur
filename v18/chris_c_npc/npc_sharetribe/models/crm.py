from odoo import models, fields, api
from datetime import datetime


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    sharetribe_id = fields.Char("Sharetribe ID", tracking=True)
    practice_state_ids = fields.Many2many(
        'res.country.state',
        relation='crm_lead_state_rel',
        string="States Needing Collaborator",
        tracking=True)
    summary = fields.Text("Professional Summary", tracking=True)
    license_type = fields.Char("License", tracking=True)
    years_experience = fields.Char("Years of Experience", tracking=True)
    availability_start = fields.Char("Start Date", tracking=True)
    availability_start_pub = fields.Char("pub_start_date", tracking=True)
    has_linkedin = fields.Boolean("Has LinkedIn", tracking=True)
    linkedin_url = fields.Char("LinkedIn URL", tracking=True)
    work_history_ids = fields.One2many(
        'npc_sharetribe.work_history', 'lead_id', "Work History")
    custom_user_referral = fields.Char("User Referral", tracking=True)
    custom_last_stage_changed_date = fields.Datetime("Last Stage Change Date", compute="_compute_custom_last_stage_changed_date", store=True)
    custom_sch_zoom_call_date = fields.Datetime("Scheduled zoom call", compute="_compute_custom_invoice_sent_date", store=True)
    custom_invoice_sent_date = fields.Datetime("Invoice Sent", compute="_compute_custom_invoice_sent_date", store=True)
    custom_contract_sent_date = fields.Datetime("Contract Sent", compute="_compute_custom_invoice_sent_date", store=True)
    custom_all_contracts_signed2 = fields.Datetime("All Contracts Signed", compute="_compute_custom_invoice_sent_date")
    custom_stage_duration_hours = fields.Float(
        string="Hours in Current Stage",
        compute="_compute_custom_stage_duration_hours",
        store=False  # optional; store=True if you want to use it in filters
    )
    first_payment_date = fields.Date("First Payment Date", compute="_compute_invoice_payment_dates", store=True)
    second_payment_date = fields.Date("Second Payment Date", compute="_compute_invoice_payment_dates", store=True)
    favorites_ids = fields.Many2many(string="Favorites", comodel_name='npc.favorites', relation='crm_lead_npc_favorite_rel', tracking=True)
    calendlyintialisation = fields.Text("Calendly Initialisation", readonly=True)
    calendlyintialisation_url = fields.Char("Calendly Initialisation URL", readonly=True)
    calendlyintialisation_date = fields.Datetime("Calendly Initialisation Date", readonly=True)

    custom_sch_zoom_call_date_alternative = fields.Datetime(
        "Alternate scheduled zoom call",
    )

    custom_calendly_qa_ids = fields.One2many('npc.calendly.qa', 'crm_id', string='Calendly Q&A')
    lost_reason_id = fields.Many2one('crm.lost.reason', "Lost Reason")
    active_status_label = fields.Char(
        string="Status",
        compute="_compute_active_status",
        store=False
    )

    def _compute_active_status(self):
        for rec in self:
            rec.active_status_label = "ACTIVE" if rec.active else "LOST"

    @api.depends('message_ids', 'custom_sch_zoom_call_date_alternative')
    def _compute_custom_invoice_sent_date(self):
        invoice_stage = self.env['crm.stage'].search([('name', '=', 'Invoice sent')], limit=1)
        contract_stage = self.env['crm.stage'].search([('name', '=', 'Contracts sent')], limit=1)
        sch_zoom_call_stage = self.env['crm.stage'].search([('name', '=', 'Scheduled zoom call')], limit=1)
        for lead in self:
            lead.custom_invoice_sent_date = False
            lead.custom_contract_sent_date = False
            # Find mail.message entries where stage_id changed to this stage
            messages = self.env['mail.message'].search([
                ('model', '=', 'crm.lead'),
                ('res_id', '=', lead.id),
                ('tracking_value_ids.field_id.name', '=', 'stage_id')
            ], order='create_date asc')

            # Loop through and find if the new value matches the Invoice Sent stage
            if invoice_stage:
                for msg in messages:
                    for track in msg.tracking_value_ids:
                        if track.field_id.name == 'stage_id' and track.new_value_char == invoice_stage.name:
                            lead.custom_invoice_sent_date = msg.create_date
                            break
                    if lead.custom_invoice_sent_date:
                        break
            
            if contract_stage:
                for msg in messages:
                    for track in msg.tracking_value_ids:
                        if track.field_id.name == 'stage_id' and track.new_value_char == contract_stage.name:
                            lead.custom_contract_sent_date = msg.create_date
                            break
                    if lead.custom_contract_sent_date:
                        break

            # Scheduled Zoom Call Date
            if sch_zoom_call_stage:
                for msg in messages:
                    for track in msg.tracking_value_ids:
                        if track.field_id.name == 'stage_id' and track.new_value_char == sch_zoom_call_stage.name:
                            lead.custom_sch_zoom_call_date = msg.create_date
                            break
                    if lead.custom_sch_zoom_call_date:
                        break
            if not lead.custom_sch_zoom_call_date:
                lead.custom_sch_zoom_call_date = lead.custom_sch_zoom_call_date_alternative

            # -------------- Adjusted Signing Logic Begins Here --------------

            # Fetch all signed sign.request items for this partner
            sign_items = self.env['sign.request.item'].search([('partner_id', '=', lead.partner_id.id)])
            sign_requests = sign_items.mapped('sign_request_id')
            signed_requests = sign_requests.filtered(lambda s: s.state == 'signed')
            if sign_requests:
                if any(x.state != 'signed' for x in sign_requests):
                    lead.custom_all_contracts_signed2 = False

            # Only set if all sign_request_ids are signed
            # Option A: If at least one sign request exists and all are signed
            if sign_requests and len(signed_requests) == len(sign_requests):
                lead.custom_all_contracts_signed2 = signed_requests[-1].last_action_date
                all_signed_stage = self.env['crm.stage'].search([('name', '=', 'All Contracts signed')], limit=1)
                contract_sent = self.env['crm.stage'].search([('name', '=', 'Contracts sent')], limit=1)
                if all_signed_stage and contract_sent and lead.stage_id == contract_sent and lead.stage_id != all_signed_stage:
                    lead.stage_id = all_signed_stage
            else:
                lead.custom_all_contracts_signed2 = False

    @api.depends('custom_last_stage_changed_date')
    def _compute_custom_stage_duration_hours(self):
        now = fields.Datetime.now()
        for lead in self:
            if lead.custom_last_stage_changed_date:
                delta = now - lead.custom_last_stage_changed_date
                lead.custom_stage_duration_hours = round(delta.total_seconds() / 3600, 2)
            else:
                lead.custom_stage_duration_hours = 0.0

    @api.depends('message_ids')
    def _compute_custom_last_stage_changed_date(self):
        for lead in self:
            last_msg = self.env['mail.message'].search([
                ('model', '=', 'crm.lead'),
                ('res_id', '=', lead.id),
                ('tracking_value_ids.field_id.name', '=', 'stage_id')
            ], order='create_date desc', limit=1)
            lead.custom_last_stage_changed_date = last_msg.create_date if last_msg else False

    @api.depends('partner_id')
    def _compute_invoice_payment_dates(self):
        for lead in self:
            lead.first_payment_date = False
            lead.second_payment_date = False
            if not lead.partner_id:
                continue
            # Get all posted customer invoices for this partner
            invoices = self.env['account.move'].search([
                ('partner_id', '=', lead.partner_id.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
            ])
            payment_dates = []
            for invoice in invoices:
                # Find all reconciled payments for this invoice
                payment_dates.extend(invoice.matched_payment_ids.mapped('date'))
            # Sort and assign
            payment_dates = sorted(set(payment_dates))
            if payment_dates:
                lead.first_payment_date = payment_dates[0]
                if len(payment_dates) > 1:
                    lead.second_payment_date = payment_dates[1]


class WorkHistory(models.Model):
    _name = 'npc_sharetribe.work_history'
    _description = "Work History"
    _order = 'year_end desc'

    lead_id = fields.Many2one('crm.lead', "Lead")
    name = fields.Char("Title", required=True)
    year_start = fields.Char("Start Year")
    year_end = fields.Char("End Year")
    month_start = fields.Char("Start Month")
    month_end = fields.Char("End Month")
    is_current = fields.Boolean("Is Current")
    description = fields.Text("Description")
    location = fields.Char("Location")
    company = fields.Char("Company")
