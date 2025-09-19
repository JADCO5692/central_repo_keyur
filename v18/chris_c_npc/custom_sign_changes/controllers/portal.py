from odoo import http
from odoo.http import request

from odoo.addons.payment.controllers.portal import PaymentPortal

class Portal(PaymentPortal):

    @http.route('/my/payment_method', type='http', methods=['GET'], auth='user', website=True)
    def payment_method(self, **kwargs):
        res = super().payment_method(**kwargs) 
        docs = request.env['sign.request'].sudo().get_sign_attechment_ids() 
        if docs:
            res.qcontext.update({
                'docs': request.env['ir.attachment'].sudo().browse(docs)
            })
        return res

class SalesDashboard(http.Controller):

    @http.route('/my/attachment/download/<int:attachment_id>', type='http', auth='user')
    def download_attachment(self, attachment_id, **kwargs):
        attachment = request.env['ir.attachment'].sudo().browse(attachment_id)
        if not attachment.exists():
            return request.not_found()
        filecontent = attachment.sudo().raw or attachment.sudo().datas
        return request.make_response(
            filecontent,
            headers=[
                ('Content-Type', attachment.mimetype or 'application/octet-stream'),
                ('Content-Disposition', f'attachment; filename="{attachment.name}"')
            ]
        ) 