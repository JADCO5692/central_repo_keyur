from odoo import models, fields, api, _
from odoo.tools import float_round
import logging

_logger = logging.getLogger(__name__)


SUBSCRIPTION_STATES = [
    ('1_draft', 'Quotation'),  # Quotation for a new subscription
    ('2_renewal', 'Renewal Quotation'),  # Renewal Quotation for existing subscription
    ('3_progress', 'In Progress'),  # Active Subscription or confirmed renewal for active subscription
    ('4_paused', 'Paused'),  # Active subscription with paused invoicing
    ('5_renewed', 'Renewed'),  # Active or ended subscription that has been renewed
    ('6_churn', 'Churned'),  # Closed or ended subscription
    ('7_upsell', 'Upsell'),  # Quotation or SO upselling a subscription
]

class SaleCommissionLogs(models.Model):
    _name = 'sale.commission.logs'
    _description = 'Creates the commision log from lead'
 
    # Basic Info
    name = fields.Char('Log Name')
    lead_id = fields.Many2one('crm.lead', 'Opportunity')
    salesperson_id = fields.Many2one('res.users', 'Salesperson', related='lead_id.user_id')
    npc_user_type = fields.Selection([
        ('APP', 'Nurse Practitioner/PA'),
        ('PHYS', 'Physician')
    ], string='User Type')
    subscription_status = fields.Selection(SUBSCRIPTION_STATES, 'Subscription Status')
    
    # NP (Nurse Practitioner) Info
    np_partner_id = fields.Many2one('res.partner', 'NP Name')
    np_email = fields.Char('NP Email')
    np_phone = fields.Char('NP Phone')
    np_advance_practice_provider = fields.Many2one('res.partner', 'Advance Practice Provider', related='np_partner_id')
    np_state = fields.Many2many('res.country.state', 'NP State', related='lead_id.practice_state_ids')
    
    # Practice Info
    practice_type_ids = fields.Many2many('npc_crm.practice_type', string="Practice Types")
    effective_date = fields.Date('Effective Date')
    subscription_pause_date = fields.Date('Pause Date')
    
    # Collaborator / Physician Info
    collaborator_id = fields.Many2one('res.partner', 'Collaborator')  # Physician
    
    # Financials - Monthly Totals
    crm_fee_line_id = fields.Many2one('npc_crm.physician', 'Fee Line ID')  # Opportunity Fee Line ID
    np_monthly_total = fields.Float('Monthly total')
    physician_monthly_fee = fields.Float('Physician Monthly fee')
    physician_fee = fields.Float('Physician fee')
    npc_monthly_fee = fields.Float('NPC Monthly Fee')
    npc_fee = fields.Float('NPC Fee')
    prorate_percentage = fields.Float('Prorate %')
    
    # Financials - First Month Breakdown
    first_month_total = fields.Float('First Monthly total')
    first_month_physician_fee = fields.Float('First Physician Fee')
    first_month_npc_fee = fields.Float('First NPC Fee')
    
    # Order & Invoice Info
    order_name = fields.Char('Origin')
    order_id = fields.Many2one('sale.order', 'Sale Order')
    invoice_id = fields.Many2one('account.move', 'Invoice')
    invoice_date = fields.Date('Invoice Date', related='invoice_id.invoice_date')
    invoice_date_due = fields.Date('Due Date', related='invoice_id.invoice_date_due')
    custom_contract_end_date = fields.Date('Contract End Date', related='invoice_id.custom_contract_end_date')

    def get_invoices(self, commission_logs):
        moves_obj = self.env['account.move']
        invoices = moves_obj.search([
            ('payment_state', 'in', ['paid', 'in_payment', 'not_paid', 'partial']),
            ('move_type', '=', 'out_invoice'),
            ('commission_id', '=', False),
            ('is_commission_excluded', '=', False),
            ('state', 'not in', ['cancel','draft']),
        ])

        invoices_to_return = moves_obj
        for inv in invoices:
            if inv.custom_lead_id or inv.custom_lead_id2:
                invoices_to_return += inv
                _logger.info("Invoice - Start")
                _logger.info(inv)
                _logger.info(inv.name)
                _logger.info("Invoice - End")
        if invoices_to_return:
            _logger.info(f'total invoice {len(invoices_to_return)}')
        return invoices_to_return if invoices_to_return else invoices_to_return

    def create_commition_logs(self):
        commission_log_obj = self.env['sale.commission.logs']
        commission_logs = commission_log_obj.sudo().search([]).mapped('order_name')
        invoices = self.get_invoices(commission_logs)
        # Extract all unique invoice origins that are not empty
        invoice_origins = list(set(
            inv.invoice_origin for inv in invoices if inv.invoice_origin
        ))
        
        # Search all matching sale orders in one query
        sale_orders = self.env['sale.order'].search([
            ('name', 'in', invoice_origins),
            ('state', '=', 'sale'),
        ])
        # Build cache {invoice_origin: sale_order}
        sale_order_cache = {so.name: so for so in sale_orders}
        
        for invoice in invoices:
            lead_id = invoice.custom_lead_id
            if not lead_id:
                lead_id = invoice.custom_lead_id2
            if lead_id:
                collaborators = lead_id.physician_ids 
                sale_order = False
                sale_order = sale_order_cache.get(invoice.invoice_origin)
                 
                # subscription status
                subscription_state = ''
                subsc_pause_date = False
                
                first_month_total = 0
                first_month_physician_fee = 0
                first_month_npc_fee = 0
                first_invoice = False
                    
                if sale_order:
                    np_partner = sale_order.partner_id 
                    if sale_order.np_partner_id:
                        np_partner = sale_order.np_partner_id
                    
                    if sale_order and sale_order.is_subscription:
                        subscription_state = sale_order.subscription_state
                        if sale_order.subscription_state == '4_paused':
                            subsc_pause_date = sale_order.subscription_pause_date
                     
                    # calc first invoice data
                    if sale_order and sale_order.invoice_ids:
                        first_invoice = sale_order.invoice_ids.sorted('create_date')[:1]
                else:
                    np_partner = invoice.partner_id
                    first_invoice = invoice
                
                if sale_order or invoice.custom_lead_id2:
                    total_colabs = len(collaborators) 
                    divided_npc_fee = 0
                    divided_physician_fee = 0

                    total_collab_fee = sum(c.collab_fee for c in collaborators)
                    total_npc_fee = sum(c.npc_fee for c in collaborators)

                    # calc current invoice commistions
                    npc_total = sum(
                        line.price_subtotal
                        for line in invoice.invoice_line_ids
                        if line.product_id.is_np_fees_product
                    )
                    
                    phy_total = sum(
                        line.price_subtotal
                        for line in invoice.invoice_line_ids
                        if line.product_id.is_physician_fees_product
                    )

                    for i, colabs in enumerate(collaborators): 
                         
                        physician_fee = 0
                        npc_fee = 0 
                        npc_monthly_total = 0  
                        physician_monthly_fee = colabs.collab_fee
                        npc_monthly_fee = colabs.npc_fee
                        npc_factor = 1
                        if npc_total:
                            if total_npc_fee:
                                npc_factor = npc_monthly_fee / total_npc_fee
                                if i != total_colabs -1:
                                    npc_fee = npc_factor * npc_total
                                else: 
                                    npc_fee = npc_total - divided_npc_fee
                                divided_npc_fee += npc_fee
                                npc_monthly_total += npc_fee
                            else:
                                npc_fee = -1000

                        phy_factor = 1
                        if phy_total:
                            if total_collab_fee:
                                phy_factor = physician_monthly_fee / total_collab_fee
                                if i != total_colabs -1:
                                    physician_fee = phy_factor * phy_total
                                else: 
                                    physician_fee = phy_total - divided_physician_fee
                                divided_physician_fee += physician_fee 
                                npc_monthly_total += physician_fee
                            else:
                                physician_fee = -1000
                        #==================================
                        # get first month invoice commiss...
                        if first_invoice and first_invoice.id != invoice.id:
                            first_month_physician_fee, first_month_npc_fee = self.get_first_commission_fees(first_invoice,colabs)
                        else:
                            first_month_physician_fee, first_month_npc_fee = physician_fee, npc_fee
                        log_values = {
                            # Invoice & Order Info
                            'invoice_id': invoice.id,
                            'order_name': invoice.invoice_origin,
                            'order_id': sale_order.id if sale_order else False,
                            
                            # NP Partner Info
                            'np_partner_id': np_partner and np_partner.id,
                            'np_phone': np_partner and np_partner.phone,
                            'np_email': np_partner and np_partner.email,
                            'np_advance_practice_provider': np_partner and np_partner.id,
                            'npc_user_type': lead_id.npc_user_type,
                        
                            # Fee Totals
                            'np_monthly_total': npc_monthly_total,
                            'physician_monthly_fee': physician_monthly_fee,
                            'physician_fee': physician_fee,
                            'npc_monthly_fee': npc_monthly_fee,
                            'npc_fee': npc_fee,
                            'prorate_percentage': round((physician_fee / physician_monthly_fee), 2) if physician_monthly_fee > 0 else 0,
                            'crm_fee_line_id': colabs.id,
                        
                            # First Month Breakdown
                            'first_month_total': first_month_physician_fee + first_month_npc_fee,
                            'first_month_physician_fee': first_month_physician_fee,
                            'first_month_npc_fee': first_month_npc_fee,
                        
                            # Collaborator Info
                            'collaborator_id': colabs.name.id,
                        
                            # Subscription Info
                            'effective_date': sale_order and sale_order.start_date,
                            'subscription_pause_date': subsc_pause_date,
                            'subscription_status': subscription_state,
                        
                            # Lead Info
                            'practice_type_ids': lead_id.practice_type_ids.ids if lead_id.practice_type_ids else [],
                            'lead_id': lead_id.id if lead_id else False,
                        }
  
                        commission_log_obj = commission_log_obj.create(log_values)
        self.env.cr.commit()
                    
    def get_first_commission_fees(self,invoice,collaborator):
        lead_id = invoice.custom_lead_id
        first_month_physician_fee = 0
        first_month_npc_fee = 0
        if not lead_id:
            return first_month_physician_fee, first_month_npc_fee
        
        collaborators = lead_id.physician_ids
        total_colabs = len(collaborators)
        total_collab_fee = sum(c.collab_fee for c in collaborators)
        total_npc_fee = sum(c.npc_fee for c in collaborators)
        npc_total = sum(
            line.price_subtotal
            for line in invoice.invoice_line_ids.filtered(
                lambda l: l.product_id.is_np_fees_product
            )
        )
        
        phy_total = sum(
            line.price_subtotal
            for line in invoice.invoice_line_ids.filtered(
                lambda l: l.product_id.is_physician_fees_product
            )
        )

        for i, colabs in enumerate(collaborators):
            if colabs.id == collaborator.id: 
                physician_monthly_fee = colabs.collab_fee
                npc_monthly_fee = colabs.npc_fee  
                if npc_total:
                    npc_factor = 1
                    if total_npc_fee:
                        npc_factor = npc_monthly_fee / total_npc_fee
                        first_month_npc_fee = npc_factor * npc_total
                    else:
                        first_month_npc_fee = -1000

                phy_factor = 1
                if phy_total:
                    if total_collab_fee:
                        phy_factor = physician_monthly_fee / total_collab_fee
                        first_month_physician_fee = phy_factor * phy_total
                    else:
                        total_collab_fee = -1000
                            
        return first_month_physician_fee, first_month_npc_fee
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('commission_logs') or _("New")
        return super(SaleCommissionLogs, self).create(vals_list)
        
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        # Now call the super method
        result = super().read_group(
            domain,
            fields,
            groupby,
            offset=offset,
            limit=limit,
            orderby=orderby,
            lazy=lazy,
        )

        is_avg_needed = 'prorate_percentage:sum' in fields
        if is_avg_needed:
            for line in result:
                if "__domain" in line:
                    lines = self.search(line["__domain"])
                    total = sum(lines.mapped('prorate_percentage'))
                    count = len(lines)
                    average = float_round((total / count) if count else 0.0, precision_digits=2)
                    line["prorate_percentage"] = average
        return result
