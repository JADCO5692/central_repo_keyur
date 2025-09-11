from odoo import models, fields, api,_
from calendar import monthrange,calendar
from datetime import date
from odoo.exceptions import ValidationError
from collections import defaultdict
import calendar

class AccountMove(models.Model):
    _inherit = "account.move"

    custom_lead_id = fields.Many2one('crm.lead', string="Opportunity", compute="_compute_custom_lead_id")
    custom_lead_id2 = fields.Many2one('crm.lead', string="Alternate Opportunity")
    np_partner_id = fields.Many2one('res.partner','NP Partner')
    custom_contract_end_date = fields.Date('MD Stop Date')

    # Track related vendor bills
    vendor_bill_ids = fields.One2many('account.move', 'source_invoice_id',
                                      string='Related Vendor Bills',
                                      domain=[('move_type', '=', 'in_invoice')])

    vendor_bill_count = fields.Integer(compute='_compute_vendor_bill_count')
    source_invoice_id = fields.Many2one('account.move',
                                        string='Source Invoice')

    related_invoice_count = fields.Integer(string="Related Invoices", compute='compute_related_invoice_count')

    @api.depends('invoice_line_ids.vendor_bill_id')
    def compute_related_invoice_count(self):
        for record in self:
            related_invoices = self.env['account.move.line'].search([('vendor_bill_id', 'in', record.ids)]).move_id
            record.related_invoice_count = len(related_invoices)

    @api.depends('vendor_bill_ids')
    def _compute_vendor_bill_count(self):
        for record in self:
            record.vendor_bill_count = len(record.vendor_bill_ids)

    def action_view_vendor_bills(self):
        """Action to view related vendor bills"""
        vals = {
            'type': 'ir.actions.act_window',
            'name': 'Related Vendor Bills',
            'res_model': 'account.move',
            'domain': [('id', 'in', self.vendor_bill_ids.ids)],
            'view_mode': 'list,form' if len(self.vendor_bill_ids) > 1 else 'form',
            'target': 'current',
        }
        if len(self.vendor_bill_ids) == 1:
            vals['res_id'] = self.vendor_bill_ids[0].id
        return vals
    
    def _compute_custom_lead_id(self):
        for rec in self:
            lead = False  
            sale_lines = rec.line_ids.mapped('sale_line_ids')
            sale_order = sale_lines.mapped('order_id')[:1]
            rec.np_partner_id = sale_order.np_partner_id if sale_order else False
            if sale_order and sale_order.opportunity_id:
                lead = sale_order.opportunity_id.id
            if rec.invoice_origin and not lead:
                so = self.env['sale.order'].sudo().search([('name', '=', rec.invoice_origin)], limit=1)
                if so and so.opportunity_id:
                    lead = so.opportunity_id.id 
            rec.custom_lead_id = lead

    def create(self,vals):
        invoices = super(AccountMove,self).create(vals)
        for rec in invoices:
            order = self.env['sale.order'].sudo().search([('name','=',rec.invoice_origin)]) 
            if order and order.next_invoice_date:
                rec.invoice_date = order.next_invoice_date
                rec.invoice_date_due = order.next_invoice_date
                if order:
                    rec._adjust_npc_fee_on_invoice(order)
        return invoices
        
    @api.onchange("custom_contract_end_date")
    def _onchange_custom_contract_end_date(self):
        for record in self:
            if record.custom_contract_end_date and record.invoice_date_due:
                # Rule 1: Contract end date must be greater than invoice_date_due
                if record.custom_contract_end_date <= record.invoice_date_due:
                    raise ValidationError("Contract End Date must be greater than the Invoice Date.")

                # Rule 2: Must be within same month/year as invoice_date_due
                if (record.custom_contract_end_date.month != record.invoice_date_due.month or
                        record.custom_contract_end_date.year != record.invoice_date_due.year):
                    raise ValidationError("Contract End Date must be within the same month as the Invoice Date.")

                # Recompute physician fee lines if date is filled
                record._recompute_physician_and_np_fee_lines()
                
    def _recompute_physician_and_np_fee_lines(self):
        """Prorate physician fee lines, collect total reduction, and shift it into a single NP fees line."""
        for move in self:
            if not (move.invoice_date_due and move.custom_contract_end_date):
                continue

            start_date = move.invoice_date_due
            end_date = move.custom_contract_end_date

            # last day of invoice_date_due's month
            last_day = date(start_date.year, start_date.month,
                            monthrange(start_date.year, start_date.month)[1])

            # base period = from start_date until last_day of month (inclusive)
            base_days = (last_day - start_date).days + 1

            # eligible days = from start_date until contract_end_date (inclusive)
            eligible_days = (end_date - start_date).days + 1
            if eligible_days < 0:
                eligible_days = 0

            total_reduced = 0.0

            # Step 1: Prorate physician fee lines
            for line in move.invoice_line_ids.filtered("product_id.is_physician_fees_product"):
                full_amount = line.price_unit * line.quantity
                prorated_amount = (full_amount / base_days) * eligible_days

                reduced_amount = full_amount - prorated_amount
                total_reduced += reduced_amount

                line.update({
                    "price_unit": prorated_amount / line.quantity if line.quantity else prorated_amount,
                })

            # Step 2: Add reduced amount to a single NP fee line
            if total_reduced > 0:
                np_line = move.invoice_line_ids.filtered("product_id.is_np_fees_product")[:1]
                if np_line:
                    np_full_amount = np_line.price_unit * np_line.quantity
                    new_amount = np_full_amount + total_reduced
                    np_line.update({
                        "price_unit": new_amount / np_line.quantity if np_line.quantity else new_amount,
                    })

    def action_create_vendor_bill(self):
        """Wizard to select vendors and create vendor bills"""
        self.ensure_one()
        invoice_line_ids = self.invoice_line_ids.filtered(lambda line: not line.vendor_bill_id)
        return {
            'name': 'Select Vendors for Vendor Bills',
            'type': 'ir.actions.act_window',
            'res_model': 'vendor.selection',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'invoice_line_ids': invoice_line_ids.ids,
            },
        }

    def action_view_related_invoices(self):
        self.ensure_one()
        invoice = self.env['account.move.line'].search([('vendor_bill_id','in',self.ids)]).move_id
        if not invoice:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': 'No related invoices found.',
                }
            }
        vals = {
            'type': 'ir.actions.act_window',
            'name': 'Related Vendor Bills',
            'res_model': 'account.move',
            'domain': [('id', 'in', invoice.ids)],
            'view_mode': 'list,form' if len(invoice) > 1 else 'form',
            'target': 'current',
        }
        if len(invoice) == 1:
            vals['res_id'] = invoice[0].id
        return vals
    def _action_create_vendor_bill(self, vendor_id, invoice_line_ids):
        """Create vendor bills based on vendors selected in invoice lines"""
        if not invoice_line_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': 'No invoice lines found to create vendor bills.',
                }
            }

        # Group lines by vendor
        vendor_lines = defaultdict(list)
        lines_without_vendor = []

        for line in invoice_line_ids:
            if vendor_id:
                vendor_lines[vendor_id].append(line)
            else:
                lines_without_vendor.append(line)

        if not vendor_lines:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': 'No vendors found in invoice lines.',
                }
            }

        created_bills = []

        # Create vendor bills for each vendor
        for vendor, lines in vendor_lines.items():
            bill_vals = self._prepare_vendor_bill_vals(vendor, lines)
            vendor_bill = self.env['account.move'].create(bill_vals)
            for line in lines:
                line.vendor_bill_id = vendor_bill.id
            created_bills.append(vendor_bill)

            # Link the vendor bill to the original invoice
            self._link_vendor_bill(vendor_bill)

        # Show notification with results
        message = f"Successfully created {len(created_bills)} vendor bill(s) for vendors: {', '.join([bill.partner_id.name for bill in created_bills])}"
        if lines_without_vendor:
            message += f"\n{len(lines_without_vendor)} line(s) without vendor were skipped."

        return self.action_view_vendor_bills()

    def _prepare_vendor_bill_vals(self, vendor, lines):
        """Prepare values for creating vendor bill"""
        bill_lines = []

        for line in lines:
            bill_line_vals = {
                'product_id': line.product_id.id if line.product_id else False,
                'name': line.name or line.product_id.name,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
                'account_id': line.account_id.id,
                'tax_ids': [(6, 0, line.tax_ids.ids)] if line.tax_ids else False,
                'analytic_distribution': line.analytic_distribution,
                'original_invoice_line_id': line.id,
            }
            bill_lines.append((0, 0, bill_line_vals))

        return {
            'move_type': 'in_invoice',  # Vendor bill
            'partner_id': vendor.id,
            'invoice_date': fields.Date.context_today(self),
            'ref': f"Bill from {self.name}",
            'invoice_line_ids': bill_lines,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'source_invoice_id': self.id,
        }

    def _link_vendor_bill(self, vendor_bill):
        """Link vendor bill to original invoice (optional - for tracking)"""
        vendor_bill.message_post(body=_("Created from in %s", self._get_html_link()))

        self.message_post(body=_("Created from in %s", vendor_bill._get_html_link()))

    def _adjust_npc_fee_on_invoice(self, subscription):
        for inv in self:
            for line in inv.invoice_line_ids:
                fee = line.price_unit
                inv_count = subscription.invoice_count
                months = subscription.npc_fees_waiver_months
                start = subscription.start_date
                end = subscription.end_date
                nxt = subscription.next_invoice_date
                if line.product_id.is_np_fees_product and subscription.npc_fees_waiver_months:

                    # Zero fee during waiver period
                    if inv_count <= months:
                        line.price_unit = 0.0
                        continue

                    # Prorate in first invoice after waiver months
                    if inv_count == months + 1 and start:
                        if end and (nxt.year == end.year and nxt.month == end.month) and subscription.npc_fees_waiver_days and subscription.npc_fees_waiver_days < end.day:
                            days_in_end_month = calendar.monthrange(end.year, end.month)[1]
                            used_days = end.day - subscription.npc_fees_waiver_days
                            prorated_amount = round(fee * used_days / days_in_end_month, 2)
                            expire_date = date(end.year, end.month, subscription.npc_fees_waiver_days)
                            line.price_unit = prorated_amount
                            line.name = f"{used_days} days {expire_date.strftime('%m/%d/%Y')} to {end.strftime('%m/%d/%Y')}"
                            continue
                        elif  end and (nxt.year == end.year and nxt.month == end.month) and subscription.npc_fees_waiver_days and subscription.npc_fees_waiver_days > end.day:
                            line.price_unit = 0.0
                            line.name = f"Waiver until {end.strftime('%m/%d/%Y')}"
                            continue

                        else:
                            days_in_start_month = calendar.monthrange(start.year, start.month)[1]
                            used_days = days_in_start_month - subscription.npc_fees_waiver_days
                            expire_date = date(nxt.year, nxt.month, subscription.npc_fees_waiver_days)
                            prorated_amount = round(fee * used_days / days_in_start_month, 2)
                            line.price_unit = prorated_amount
                            line.name = f"{used_days} from {expire_date.strftime('%m/%d/%Y')}"
                            continue

                    # If final invoice is in the same month as end_date, prorate up to end_date
                    if end and nxt and (end.year == nxt.year and end.month == nxt.month):
                        days_in_month = calendar.monthrange(end.year, end.month)[1]
                        used_days = end.day
                        prorated = round(fee * used_days / days_in_month, 2)
                        line.price_unit = prorated
                        line.name = f"{used_days} days {nxt.strftime('%m/%d/%Y')} to {end.strftime('%m/%d/%Y')}"
                        continue

                    line.price_unit = fee

                if line.product_id.is_np_fees_product or line.product_id.is_physician_fees_product:
                    if end and nxt and (end.year == nxt.year and end.month == nxt.month):
                        days_in_month = calendar.monthrange(end.year, end.month)[1]
                        used_days = end.day
                        prorated = round(fee * used_days / days_in_month, 2)
                        line.price_unit = prorated
                        line.name = f"{used_days} days {nxt.strftime('%m/%d/%Y')} to {end.strftime('%m/%d/%Y')}"
                        continue

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    vendor_id = fields.Many2one('res.partner', string="Vendor")
    lead_partner_ids = fields.Many2many('res.partner', string='Physicians', compute='_compute_lead_partner_ids')
    original_invoice_line_id = fields.Many2one('account.move.line',
                                               string='Original Invoice Line')
    vendor_bill_id = fields.Many2one('account.move', string='Vendor Bill',
                                               domain=[('move_type', '=', 'in_invoice')])

    def _compute_lead_partner_ids(self):
        for line in self:
            line.lead_partner_ids = False
            if line.move_id and line.move_id.custom_lead_id:
                lead = line.move_id.custom_lead_id
                line.lead_partner_ids = [(6,0,lead.physician_partner_ids.ids)]
            elif line.move_id and line.move_id.custom_lead_id2:
                lead = line.move_id.custom_lead_id2
                line.lead_partner_ids = [(6,0,lead.physician_partner_ids.ids)]
