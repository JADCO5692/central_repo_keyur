from odoo import models, fields,_
from odoo.exceptions import ValidationError
import json 
from datetime import datetime
from dateutil import parser 
import pytz
import logging

utc = pytz.utc
_logger = logging.getLogger(__name__)

class PmallOrderLogs(models.Model):
    _name = 'pmall.order.logs'
    _description = "Pmall order logs"
    _rec_name = 'order_number'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char('Name',default="Pmall Order log",tracking=True)
    pmall_config_id = fields.Many2one('pmall.config','Pmall Config')
    pmall_order_context = fields.Text('Pmall Order Context',tracking=True)
    status = fields.Selection([('new','New'),('synced','Synced'),('failed','Failed'),('cancelled','Cancelled')],default='new',string='Status',tracking=True)
    batch_number = fields.Char('Batch Number',tracking=True)
    order_number = fields.Char('Pmall Order Number')
    order_id = fields.Many2one('sale.order','Related Sale Order',tracking=True)
    error_logs_count = fields.Integer('Error Logs',compute="_compute_error_logs")
    active = fields.Boolean("active",default=True)
    ship_status = fields.Char('Ship Status')
    
    def create_order_logs(self,config,order_batches):
        status = config.shipping_status.mapped('tech_name')
        for batch in order_batches:
            for order in batch.get('orders'):
                if order.get('currentStatus') in status:
                    existing_order_logs = self.search([('order_number','=',order.get('orderNumber'))],limit=1)
                    if len(existing_order_logs) and existing_order_logs.status == 'synced':
                        if not existing_order_logs.order_id:
                            self.create({
                                'pmall_config_id':config.id,
                                'pmall_order_context':json.dumps(order),
                                'batch_number':batch.get('batchNumber'),
                                'order_number':order.get('orderNumber'),
                                'ship_status':order.get('currentStatus')
                            })
                    elif not len(existing_order_logs):
                        self.create({
                            'pmall_config_id':config.id,
                            'pmall_order_context':json.dumps(order),
                            'batch_number':batch.get('batchNumber'),
                            'order_number':order.get('orderNumber'),
                            'ship_status':order.get('currentStatus')
                        })
                    else:
                        continue

    def _compute_error_logs(self):
        for rec in self:
            err_logs = self.env['order.create.error.log'].sudo().search([('order_log_id','in',rec.ids)])
            if err_logs:
                rec.error_logs_count = len(err_logs)
            else:
                rec.error_logs_count = 0

    def chron_sync_to_odoo(self):
        logs = self.search([('status','=','new'),('order_id','=',False)])
        logs.sync_to_odoo()

    def sync_to_odoo(self): 
        SaleOrder = self.env['sale.order'].sudo()
        Product = self.env['product.product'].sudo()
        ProductMapping = self.env['pmall.product.mapping'].sudo()
        order_err_log_obj = self.env['order.create.error.log'].sudo()
        route_obj = self.env.ref("custom_dropstitch.record_custom_route")
        for rec in self:
            order_context = json.loads(rec.pmall_order_context)
            order_number = order_context.get('orderNumber')
            giftMessage = order_context.get('giftMessage')
            order_items_len = order_context.get('orderItem', [])
            exist_order = SaleOrder.search([('name','=',order_number)])
            if rec.order_id or exist_order: 
                # error_msg = f"Order log({order_number}) already synced in odoo please check order {(rec.order_id and rec.order_id.name) or (exist_order and exist_order.name)}." 
                rec.status = 'synced'
                rec.order_id = (rec.order_id and rec.order_id[0].id) or (exist_order and exist_order[0].id)
                # raise ValidationError(error_msg)
                continue
            try:  
                order_date_str = order_context.get('orderDate', '')
                date_order = False
                if order_date_str:
                    # Remove 'Z' if present and limit microseconds to 6 digits
                    if '.' in order_date_str:
                        date_part, frac = order_date_str.split('.')
                        frac = frac[:6]  # limit to 6 digits
                        clean_date_str = f"{date_part}.{frac}"
                    else:
                        clean_date_str = order_date_str
                
                    date_order = datetime.fromisoformat(clean_date_str)
                else:
                    date_order = False
                    
                order_vals = {
                    'name': order_number,
                    'pmall_order_number': order_number,
                    'partner_id': rec.pmall_config_id.for_partner_id.id,
                    'pmall_order_date': order_context.get('orderDate'), 
                    'pmall_order_log_id': rec.id, 
                    'custom_policy': 'intent',
                    'is_pmall_order': True,
                    'custom_dropship_order': True, 
                    'custom_gift_mess': giftMessage,
                }

                order_lines = []
                for item in order_context.get('orderItem', []):
                    sku = (item.get('partnerSku') or item.get('sku') or '').strip()
                    field_value = next(
                        (i for i in item.get('personalization', []) if i.get('fieldName') == "Choose Color"),
                        None
                    )
                    if not field_value:
                        field_value = next(
                            (i for i in item.get('personalization', []) if i.get('fieldName') == "Select Color"),
                            None
                        )
                    field_value = (field_value.get('fieldValue') if field_value else '').strip()
                
                    # Only join if field_value exists
                    sku = f"{sku} {field_value}".strip()

                    product = Product.search([('default_code', '=', sku.strip())], limit=1) 
                    if not len(product):
                        order_err_log_obj.create({
                            'name':'Error during Product fetch',
                            'batch_id':rec.batch_number, 
                            'order_number':order_number,
                            'partner_sku':sku,
                            'order_log_id':rec.id,
                            'error_log':f'Product with partner SKU({sku.strip()}) does not exist in odoo.', 
                        })
                        rec.status = 'failed'
                        continue
                    else:
                        mapping = ProductMapping.search([('partner_sku','=',sku),('odoo_product_id','!=',False)],limit=1)
                        if not mapping:
                            ProductMapping.create({
                                'name':item.get('itemName'),
                                'partner_sku':sku,
                                'odoo_product_id':product.id,
                            })
                    qty = item.get('quantity', 1)
                    price = item.get('price', product.lst_price)
                    pls = item.get('personalization')
                    # Filter out unwanted personalization fields
                    filtered_pls = [
                        p for p in pls
                        if p.get("fieldName") and not any(
                            kw in p["fieldName"] for kw in ["Select Color", "Choose Color"]
                        )
                    ]

                    custom_tiff_file_url = item.get('productionFile')
                    name_part = item.get('itemName') or product.display_name or ''
                    order_number_str = str(order_number) if order_number is not None else ''
                    
                    route_id = route_obj.id if filtered_pls and route_obj else False
                        
                    # Build custom lines (max 3)
                    custom_lines = []
                    for idx, p in enumerate(filtered_pls[:3], start=1):
                        val = p.get("fieldValue", "")
                        if val:
                            custom_lines.append(f"\nLine {idx} :{val}")
                        else:
                            custom_lines.append("")
                    
                    custom_line1 = custom_lines[0] if len(custom_lines) > 0 else ""
                    custom_line2 = custom_lines[1] if len(custom_lines) > 1 else ""
                    custom_line3 = custom_lines[2] if len(custom_lines) > 2 else ""
                    
                    order_lines.append((0, 0, {
                        'product_id': product.id,
                        'product_uom_qty': qty,
                        'price_unit': price,
                        'name': (item.get('itemName') or product.display_name) + custom_line1 + custom_line2 + custom_line3,
                        'product_uom': product.uom_id.id,
                        "custom_line1": filtered_pls[0].get("fieldValue") if len(filtered_pls) > 0 else "",
                        "custom_line2": filtered_pls[1].get("fieldValue") if len(filtered_pls) > 1 else "",
                        "custom_line3": filtered_pls[2].get("fieldValue") if len(filtered_pls) > 2 else "",
                        "route_id": route_id,
                        'custom_tiff_file_url': custom_tiff_file_url,
                        'custom_customer_product': product.custom_customer_sku,
                    }))
                if len(order_items_len) == len(order_lines): 
                    address_ids = self.create_addresses(order_context,rec.pmall_config_id.for_partner_id)
                    order_vals.update({
                        'partner_invoice_id':rec.pmall_config_id.for_partner_id.id,
                        'partner_shipping_id':address_ids.get('ship_to_id',False),
                    })
                    SaleOrder = SaleOrder.create(order_vals)
                    if SaleOrder:
                        SaleOrder._compute_require_payment()
                        SaleOrder._compute_prepayment_percent()
                        SaleOrder._onchange_custom_partner_id()
                        SaleOrder._compute_allowed_customer_ids()
                        SaleOrder.custom_policy = 'intent'
                        
                        SaleOrder.order_line = order_lines
                        
                        for line in SaleOrder.order_line:
                            line._onchange_custom_product_no_variant_attribute_value_ids()
                            line._get_sale_order_line_multiline_description_variants()
                        SaleOrder.process_order(date_order)
                    rec.order_id = SaleOrder.id or False
                    order_err_log_obj = order_err_log_obj.search([('order_number','=',order_number)])
                    if order_err_log_obj:
                        order_err_log_obj.action_archive()
                    rec.status = 'synced'
                else:
                    continue
                
            except Exception as error:
                order_err_log_obj.create({
                    'order_log_id':rec.id,
                    'name':'Error during order sync',
                    'batch_id':rec.batch_number, 
                    'error_log':f'Error:{error}'
                })
                rec.status = 'failed'
                raise error
            
    def create_addresses(self, order_context, for_partner_id):
        partner_obj = self.env['res.partner'].sudo()
        base_domain = [('parent_id', '!=', for_partner_id.id)]

        ship_data = order_context.get('shipTo', {})
        #bill_data = order_context.get('billTo', {})

        #bill_domain = self._prepare_address_domain(bill_data)
        ship_domain = self._prepare_address_domain(ship_data)
        
        #bill_to_partner = partner_obj.search(base_domain + bill_domain, limit=1)
        #if not bill_to_partner:
        #    bill_to_partner = self._create_partner_record(bill_data,for_partner_id, 'invoice')

        ship_to_partner = partner_obj.search(base_domain + ship_domain, limit=1)
        if not ship_to_partner:
            ship_to_partner = self._create_partner_record(ship_data,for_partner_id, 'delivery')

        return {
            #'bill_to_id': bill_to_partner.id if bill_to_partner else False,
            'ship_to_id': ship_to_partner.id if ship_to_partner else False,
        }

    def _prepare_address_domain(self, data):
        country = self.env['res.country'].sudo().search([('code', '=', data.get('country', ''))], limit=1)
        return [
            ('first_name', '=', data.get('firstName', False)),
            ('last_name', '=', data.get('lastName', False)),
            ('street', '=', data.get('address1', False)),
            ('street2', '=', data.get('address2', False)),
            ('zip', '=', data.get('zipCode', False)),
            ('city', '=', data.get('city', False)),
            ('state_id', '=', False),
            ('country_id', '=', country.id if country else False),
        ]

    def _create_partner_record(self, data,parent_partner, address_type):
        country = self.env['res.country'].sudo().search([('code', '=', data.get('country', ''))], limit=1)
        name = f"{data.get('firstName', '')} {data.get('lastName', '')}".strip()
        
        vals = {
            'type': address_type,
            'parent_id':parent_partner.id,
            'name': name,
            'first_name': data.get('firstName', False),
            'last_name': data.get('lastName', False),
            'street': data.get('address1', False),
            'street2': data.get('address2', False),
            'zip': data.get('zipCode', False),
            'city': data.get('city', False),
            'state_id': False,
            'country_id': country.id if country else False,
        }

        return self.env['res.partner'].sudo().create(vals)
    
    def action_order_error_logs(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Pmall Orders Error Logs'),
            'res_model': 'order.create.error.log',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('order_log_id', 'in', self.ids)],
        }