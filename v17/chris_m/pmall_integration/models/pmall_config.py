from odoo import models, fields, _
from odoo.exceptions import ValidationError
import requests
import json
from datetime import datetime, timedelta


class PmallConfig(models.Model):
    _name = 'pmall.config' 
    _description = "configuration of pmall integration api"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
    ]
    
    name = fields.Char('Name',tracking=True)
    auth_api_url = fields.Char('Auth API URL',tracking=True) 
    pmall_dropship_api_url = fields.Char('Dropship API URL',tracking=True) 
    client_id = fields.Char('Client Id',tracking=True)
    client_secret = fields.Char('Client Secret',tracking=True)
    pmall_order_log_ids = fields.One2many('pmall.order.logs','pmall_config_id','Order Logs')
    client_access_token = fields.Char('Access Token',tracking=True)
    orders_count = fields.Integer("Orders Count",compute='_count_orders')
    fetch_orders_from_past_days = fields.Integer('Fetch order from past days',help="Enter days to fetch the orders fron past entered days")
    for_partner_id = fields.Many2one('res.partner','Partner',help="This partner will set in order create in odoo after fetch from api")
    shipping_status = fields.Many2many("shipping.status","pmall_conf_id_ship_status_id_rel","ship_status_id","pmall_conf_id",
                                    string="Sync Orders with status",help='Sync orders from api with this status',tracking=True)

    def _count_orders(self):
        for rec in self:
            rec.orders_count = len(rec.pmall_order_log_ids)

    def generate_access_token(self):
        for rec in self:
            if rec.client_secret and rec.client_id:
                pmall = rec.auth_api_url
                url = pmall + "/api/v1/OAuth/GetAccessToken?client_id="+rec.client_id+"&client_secret="+rec.client_secret 
                headers = {
                    "accept": "application/json",
                    "content-type": "application/json"
                }
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    res = json.loads(response.text)
                    rec.client_access_token = res.get('access_token')
            else:
                raise ValidationError('client ID and Client secret key is required.')

    def chron_sync_pmall_orders(self):
        for rec in self.sudo().search([],limit=1):
            rec.sync_pmall_orders()

    def sync_pmall_orders(self):
        pmall_orders_logs = self.env['pmall.order.logs'].sudo()
        for rec in self:
            if rec.client_access_token:
                days = rec.fetch_orders_from_past_days
                since_date = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"

                pmall = rec.pmall_dropship_api_url  
                token = rec.client_access_token
                url = pmall + "/api/v1/Order/GetOrders" 
                headers = {
                    "Authorization": f"Bearer {token}",
                    "accept": "application/json",
                    "content-type": "application/json"
                }
                params = {
                    "ordersUpdatedSince": since_date,
                    "productionFileFormat": 'TIFF',
                }
                response = requests.get(url,params=params, headers=headers)
                if response.status_code == 401:
                    raise ValidationError('Invalid access token. Please reset the access token')
                if response.status_code == 200:
                    if json.loads(response.text):
                        order_batches = json.loads(response.text).get('orderBatches')
                        pmall_orders_logs.create_order_logs(rec,order_batches) 


    def action_order_logs(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Pmall Orders Log'),
            'res_model': 'pmall.order.logs',
            'views': [[False, 'list'], [False, 'form']],
            'domain': [('pmall_config_id', 'in', self.ids)],
        }
 