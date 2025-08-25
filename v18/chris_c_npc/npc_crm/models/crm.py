from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)


class CRMLead(models.Model):
    _inherit = 'crm.lead'
    _order = 'probability asc, reg_date desc'

    npc_user_type = fields.Selection(
        [
            ('APP', "Nurse Practitioner/PA"),
            ('PHYS', "Physician"),
        ],
        string="User Type",
        tracking=True)
    reg_date = fields.Datetime("Registration Date", tracking=True)
    practice_type_ids = fields.Many2many('npc_crm.practice_type', string="Practice Types", tracking=True)
    npi_number = fields.Char("NPI Number", tracking=True)
    controlled_substances = fields.Boolean("Controlled Substances", tracking=True)
    physician_ids = fields.One2many(
        'npc_crm.physician',
        'lead_id',
        string="Collaborating Physicians")
    # Get all partners under collaborating physician
    physician_partner_ids = fields.Many2many("res.partner", compute="_compute_m2m_physicians",
                                             store="True", string="Collaborating Physicians")
    medium_id = fields.Many2one(help="Where you heard about us")
    signature_count = fields.Integer(compute='_compute_signature_count', default=0, string="# Signatures")
    custom_first_name = fields.Char("First Name", tracking=True)
    custom_last_name = fields.Char("Last Name", tracking=True)
   
    def write(self, vals):
        stage = vals.get('stage_id')
        if stage:
            stage_id = self.env['crm.stage'].browse(stage)
            vals['probability'] = stage_id.default_probability

        res = super().write(vals)

        # IF Contact was manually changed or npc_user_type was changed,
        # always set the NPC user type of contact to the lead's npc_user_type
        if vals.get('partner_id') or 'npc_user_type' in vals or 'type' in vals:
            for lead_id in self:
                lead_id.partner_id.npc_user_type = lead_id.npc_user_type

        return res

    def _create_customer(self):
        partner_id = super()._create_customer()

        partner_id.npc_user_type = self.npc_user_type
        if (not partner_id.custom_first_name) and self.custom_first_name:
            partner_id.custom_first_name = self.custom_first_name
        if (not partner_id.custom_last_name) and self.custom_last_name:
            partner_id.custom_last_name = self.custom_last_name

        return partner_id
    
    @api.depends('partner_id')
    def _compute_signature_count(self):
        request_item_obj = self.env['sign.request.item']
        for lead in self:
            if not lead.partner_id:
                lead.signature_count = 0
                continue

            count = request_item_obj.search_count([
                ('partner_id', '=', lead.partner_id.id),
                ('sign_request_id.state', '=', 'sent'),
            ])
            lead.signature_count = count
            
    @api.depends('physician_ids')
    def _compute_m2m_physicians(self):
        for lead in self:
            lead_physician_ids = lead.physician_ids.filtered(lambda p: not p.name and p.md_lead_id).mapped('md_lead_id.partner_id')
            partner_physician_ids = lead.physician_ids.filtered(lambda p: p.name).mapped('name')
            lead.physician_partner_ids = lead_physician_ids + partner_physician_ids
    
    def open_signatures(self):
        self.ensure_one()
        request_ids = self.env['sign.request.item'].search([('partner_id', '=', self.partner_id.id)]).mapped('sign_request_id')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Signature(s)'),
            'view_mode': 'list,kanban,form',
            'res_model': 'sign.request',
            'domain': [('id', 'in', request_ids.ids)],
            'context': {
                'search_default_reference': self.partner_id.name,
                'default_crm_signer': self.partner_id.id,
            },
        }
    
    def set_opportunity_from_lead(self):
        for lead in self.filtered(lambda l: l.type == 'opportunity' and l.team_id.id == 1):
            physician_ids = lead.physician_ids.filtered(lambda p: p.name and not p.md_lead_id)
            for physician_id in physician_ids:
                md_lead_id = self.search([('type', '=', 'opportunity'), ('npc_user_type', '=', 'PHYS'),
                                          ('partner_id', '=', physician_id.name.id)], limit=1)
                if md_lead_id:
                    physician_id.md_lead_id = md_lead_id.id


class Physician(models.Model):
    _name = 'npc_crm.physician'
    _description = "Collaborating Physicians"

    name = fields.Many2one(
        'res.partner',
        string="Physician",
        domain=[('npc_user_type', '=', 'PHYS')])
    lead_id = fields.Many2one('crm.lead', string="Lead")
    company_currency = fields.Many2one(
        'res.currency',
        string='Currency',
        related='lead_id.company_currency')
    email = fields.Char("Email", related='name.email')
    collab_fee = fields.Monetary(string="Collaboration Fee", currency_field='company_currency', default=0.0)
    npc_fee = fields.Monetary(string="NPC Fee", currency_field='company_currency', default=0.0)

    total_monthly_fee = fields.Monetary(
        string="Total Monthly Fee",
        currency_field='company_currency',
        compute='_compute_total_monthly_fee',
        store=True,
        default=0.0)
    
    md_lead_id = fields.Many2one('crm.lead', string="Physician's Lead",
                                 domain=[('type', '=', 'opportunity'), ('npc_user_type', '=', 'PHYS')])

    @api.depends('name', 'md_lead_id')
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.name.name or record.md_lead_id.name
        
    @api.depends('npc_fee', 'collab_fee')
    def _compute_total_monthly_fee(self):
        for record in self:
            collab_fee = record.collab_fee
            npc_fee = record.npc_fee
            if collab_fee and npc_fee:
                record.total_monthly_fee = collab_fee + npc_fee
            else:
                record.total_monthly_fee = collab_fee or npc_fee or 0.0
    
    @api.onchange('md_lead_id')
    def _onchange_md_lead_id(self):
        if self.md_lead_id:
            self.name = self.md_lead_id.partner_id
        else:
            self.name = False
            
    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            md_lead_id = self.env['crm.lead'].search([('type', '=', 'opportunity'), ('npc_user_type', '=', 'PHYS'),
                                      ('partner_id', '=', self.name.id)], limit=1)
            self.md_lead_id = md_lead_id and md_lead_id.id or False
        else:
            self.md_lead_id = False



class PracticeType(models.Model):
    _name = 'npc_crm.practice_type'
    _description = "Practice Type"
    _order = 'name asc'

    name = fields.Char("Practice Type", required=True)
    sequence = fields.Integer(default=1)
    color = fields.Integer("Color Index", default=0)


class CRMStage(models.Model):
    _inherit = 'crm.stage'

    default_probability = fields.Float("Default Probability", copy=False)
