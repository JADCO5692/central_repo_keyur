from odoo import fields, models, api, _
from odoo.exceptions import ValidationError 

class CustomProductBom(models.Model):
    _name = 'custom.product.bom'
    _description = 'Create product bill of metirials' 
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "utm.mixin",
    ]

    name = fields.Char(string="Sequence",default=lambda self: _("New"),required=True,copy=False,readonly=False)
    state = fields.Selection([('draft','Draft'),('completed','Completed'),('failed','Failed')],default='draft',string="Status",tracking=True)
    product_tmpl_id = fields.Many2one('product.template','Source Product Template',tracking=True)
    product_id = fields.Many2one('product.product','Source Product Variant',domain="[('product_tmpl_id','=',product_tmpl_id)]",tracking=True)
    bom_id = fields.Many2one('mrp.bom','Bill Of Material',domain="[('product_id','=',product_id)]",tracking=True)

    product_variant_ids = fields.Many2many('product.product',
                                           'custom_prod_bom_id_product_id_rel',
                                           'custom_prod_bom_id',
                                           'product_id',string='Target Product Variants',
                                           domain="[('product_tmpl_id','=',product_tmpl_id),('id','!=',product_id)]",
                                           tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            seq = (self.env["ir.sequence"].next_by_code("custom.product.bom")or "/")
            vals["name"] = seq
        return super(CustomProductBom, self).create(vals_list)

    def create_boms(self):
        bom_id = self.bom_id
        if self.state == 'completed':
            raise ValidationError('Operation already completed')
        try:
            for product in self.product_variant_ids:
                vals = {
                    'custom_bom_id': self.id,
                    'product_id': product.id,
                    'code': product.display_name}
                bom_id.copy(vals)
        except Exception as a:
            self.state = 'failed'
        self.state = 'completed'
        

