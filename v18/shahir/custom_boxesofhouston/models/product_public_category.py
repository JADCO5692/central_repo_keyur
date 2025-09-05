from odoo import models, fields

class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    is_main_parent = fields.Boolean('Is Main Parent')


    def check_more_categories(self):
        filtered_categories = self.browse()

        for rec in self: 
            if not rec.parent_id:
                if not rec.is_main_parent:
                    filtered_categories |= rec
 
            else:
                main_parent = rec
                while main_parent.parent_id:
                    main_parent = main_parent.parent_id

                if not main_parent.is_main_parent:
                    if not rec.parent_id:
                        filtered_categories |= rec

        return filtered_categories