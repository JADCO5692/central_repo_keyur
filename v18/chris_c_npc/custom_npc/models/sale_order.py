from odoo import models, api, fields
from dateutil.relativedelta import relativedelta
from datetime import date

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    np_partner_id = fields.Many2one('res.partner','NP Partner')
    npc_fees_waiver_months = fields.Integer(default=0, string="NPC Fees - Waiver Months",copy=False)
    
    npc_fees_waiver_days = fields.Integer(string="NPC Fees - Waiver Days",compute='_compute_npc_fees_waiver_days', tracking=True)
    npc_fees_waiver_start_date = fields.Date(
        string="NPC Fees Waiver Start",
        help="Date from which waiver period starts. Defaults to subscription start date.",copy=False
    )
    npc_waiver_locked = fields.Boolean(
        string="Waiver Locked",
        compute="_compute_npc_waiver_locked",
        store=True
    )

    @api.depends("invoice_ids.invoice_line_ids")
    def _compute_npc_waiver_locked(self):
        for sub in self:
            locked = False
            if sub.invoice_ids and sub.npc_fees_waiver_months:
                for inv in sub.invoice_ids:
                    if any(
                            line.product_id.is_np_fees_product and line.price_unit == 0
                            for line in inv.invoice_line_ids
                    ):
                        locked = True
                        break
            sub.npc_waiver_locked = locked

    @api.depends('npc_fees_waiver_months', 'npc_fees_waiver_start_date', 'next_invoice_date')
    def _compute_npc_fees_waiver_days(self):
        today = date.today()
        for rec in self:
            months = rec.npc_fees_waiver_months or 0
            if not rec.npc_fees_waiver_start_date and rec.npc_fees_waiver_months:
                rec.npc_fees_waiver_start_date = rec.next_invoice_date
            start = rec.npc_fees_waiver_start_date
            nxt = rec.next_invoice_date

            if months <= 0 or not start:
                rec.npc_fees_waiver_days = 0
                continue

            waiver_end = start + relativedelta(months=months)
            total_days = (waiver_end - start).days
            used_days = (nxt - start).days if nxt and nxt >= start else 0
            remaining = total_days - used_days
            rec.npc_fees_waiver_days = max(0, remaining)

    @api.onchange('opportunity_id')
    def create_sale_lines(self): 
        for rec in self: 
            if rec.opportunity_id and rec.opportunity_id.physician_ids:
                # physicial_fee =  sum(rec.opportunity_id.physician_ids.mapped('collab_fee'))
                # npc_fee =  sum(rec.opportunity_id.physician_ids.mapped('npc_fee')) 
                product_obj = self.env['product.template'].sudo()
                npc_prod_id = product_obj.search([('is_np_main_fees_product','=',True)])
                physician_prod_id = product_obj.search([('is_physician_main_fees_product','=',True)])
                line_dics = []
                for physician in rec.opportunity_id.physician_ids:
                    # Collabs line
                    if physician.name and physician.name.custom_physician_product:
                        line_dics.append((0,0,{
                            'product_id':physician.name.custom_physician_product.product_variant_id.id, 
                            'name':physician.name.custom_physician_product.name,
                            'price_unit':physician.collab_fee,
                            'product_uom_qty': 1,
                        }))
                    elif physician_prod_id:
                        line_dics.append((0,0,{
                            'product_id':physician_prod_id.product_variant_id.id, 
                            'name':physician_prod_id.name,
                            'price_unit':physician.collab_fee,
                            'product_uom_qty': 1,
                        }))
                    # NPC line
                    if npc_prod_id:
                        line_dics.append((0,0,{
                            'product_id':npc_prod_id.product_variant_id.id, 
                            'name':npc_prod_id.name,
                            'price_unit':physician.npc_fee,
                            'product_uom_qty': 1,
                        }))
                if len(line_dics):
                    rec.order_line = line_dics 

            if rec.opportunity_id:
                rec.np_partner_id = rec.opportunity_id.np_partner_id.id

    