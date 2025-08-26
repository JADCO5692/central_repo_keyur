import logging
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    _description = "Update Sales Line info"

    custom_color_2 = fields.Many2one(comodel_name="product.product", string="Color 2")
    custom_color_3 = fields.Many2one(comodel_name="product.product", string="Color 3")
    custom_color_4 = fields.Many2one(comodel_name="product.product", string="Color 4")
    custom_color_5 = fields.Many2one(comodel_name="product.product", string="Color 5")
    custom_color_6 = fields.Many2one(comodel_name="product.product", string="Color 6")
    custom_color_7 = fields.Many2one(comodel_name="product.product", string="Color 7")
    custom_prod_type = fields.Selection(
        string="Inventory Type", related="product_id.custom_prod_type"
    )
    custom_attribute_1 = fields.Many2one(
        comodel_name="product.attribute.value", string="Design 1"
    )
    custom_item_image = fields.Binary(string="Item Image")
    custom_tiff_file = fields.Binary(string="TIF File")
    custom_tiff_file_name = fields.Char(string="TIF File Name")
    custom_tiff_file_url = fields.Char(string="TIF File URL", size=150)

    custom_personalize = fields.Char("Personalize", size=80)
    custom_line1 = fields.Char("Line 1", size=80)
    custom_line2 = fields.Char("Line 2", size=80)
    custom_line3 = fields.Char("Line 3", size=80)
    custom_initials = fields.Char("Initials", size=80)
    custom_font = fields.Char(string="Font", size=80)
    custom_fontcase = fields.Char(string="Font Case", size=80)
    custom_order_no = fields.Char("Order No", size=80)
    custom_customer_product = fields.Char(string="Customer SKU")
    custom_opentext = fields.Char(string="Open Text", size=80)
    custom_etail_ticket_no = fields.Char(string="Etail Ticket No", size=80)

    qty_to_intent = fields.Float(
        string="Quantity To Intent",
        compute="_compute_qty_to_intent",
        digits="Product Unit of Measure",
        store=True,
        copy=False,
    )

    @api.onchange(
        "product_no_variant_attribute_value_ids",
        "product_uom_qty",
        "name",
        "price_subtotal",
    )
    def _onchange_custom_product_no_variant_attribute_value_ids(self):
        for line in self:
            for attribute in line:
                seq = 1
                for attribute_value in attribute.product_no_variant_attribute_value_ids:
                    if (
                        attribute_value.product_attribute_value_id.custom_product_component
                    ):
                        if (
                            line.product_id.custom_prod_type == "mtp"
                            or line.product_id.custom_prod_type == "special_mtp_var"
                            or line.product_id.custom_prod_type == "special_mtp_prod"
                        ):
                            if line.product_id.custom_color_count == "1":
                                if seq == 1:
                                    seq = 3
                            elif line.product_id.custom_color_count == "2":
                                if seq == 1:
                                    seq = 3
                                elif seq == 3:
                                    seq = 6
                            elif line.product_id.custom_color_count == "3":
                                if seq == 1:
                                    seq = 3
                                elif seq == 3:
                                    seq = 6
                                elif seq == 6:
                                    seq = 7
                            elif line.product_id.custom_color_count == "4":
                                if seq == 1:
                                    seq = 3
                                elif seq == 3:
                                    seq = 4
                                elif seq == 4:
                                    seq = 5
                                elif seq == 5:
                                    seq = 6
                            elif line.product_id.custom_color_count == "6":
                                if seq == 1:
                                    seq = 2
                                elif seq == 2:
                                    seq = 3
                                elif seq == 3:
                                    seq = 4
                                elif seq == 4:
                                    seq = 5
                                elif seq == 5:
                                    seq = 6
                                elif seq == 6:
                                    seq = 7
                            field_name = "custom_color_" + str(seq)
                            line.update(
                                {
                                    field_name: attribute_value.product_attribute_value_id.custom_product_component.id
                                }
                            )
                    else:
                        if (
                            line.product_id.custom_prod_type == "special_mtp_var"
                            or line.product_id.custom_prod_type == "special_mtp_prod"
                        ):
                            if (
                                attribute_value.product_attribute_value_id.custom_design_image
                                and attribute_value.product_attribute_value_id.attribute_id.is_special_mto_attr
                            ):
                                line.update(
                                    {
                                        "custom_item_image": attribute_value.product_attribute_value_id.custom_design_image,
                                    }
                                )
                            if (
                                attribute_value.product_attribute_value_id
                                and attribute_value.product_attribute_value_id.attribute_id.is_special_mto_attr
                            ):
                                line.update(
                                    {
                                        "custom_attribute_1": attribute_value.product_attribute_value_id.id,
                                    }
                                )
            # seq = 1
            if line.product_id.custom_prod_type == "pre_set":
                _logger.info("== It is Pre-Set")
                line.update({"custom_item_image": line.product_id.image_1920})

    @api.onchange("product_id")
    def _compute_product_customer_sku(self):
        for line in self:
            line.custom_customer_product = line.product_id.custom_customer_sku
            self.set_custome_line_values(line)

    def _prepare_invoice_line(self, **optional_values):
        move_lines = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        if move_lines:
            move_lines.update({"custom_item_image": self.custom_item_image})
        return move_lines

    def set_custome_line_values(self, line):
        ptav = (
            self.product_custom_attribute_value_ids.custom_product_template_attribute_value_id
        )
        if ptav and ptav.line_number:
            lines = 1
            while lines <= ptav.line_number:
                if lines == 3:
                    self.custom_line3 = line.custom_line3
                if lines == 2:
                    self.custom_line2 = line.custom_line2
                if lines == 1:
                    self.custom_line1 = line.custom_line1
                lines += 1

    def _get_sale_order_line_multiline_description_variants(self):
        self.ensure_one()
        ptav = (
            self.product_custom_attribute_value_ids.custom_product_template_attribute_value_id
        )
        name = "\n"
        if ptav and ptav.line_number:
            if ptav.name not in ["=", "Initials"]:
                for i in range(0, ptav.line_number):
                    if i == 0:
                        name += "Line 1 :" + (self.custom_line1 or "")
                    elif i == 1:
                        name += "Line 2 :" + (self.custom_line2 or "")
                    elif i == 2:
                        name += "Line 3 :" + (self.custom_line3 or "")
                    name += "\n"
            else:
                if ptav.name == "=":
                    name += "Personalize: " + (self.custom_personalize or "")
                elif ptav.name == "Initials":
                    name += "Initials: " + (self.custom_initials or "")
                name += "\n"
            # set custom route while preparing custom line inputs
            route_obj = self.env.ref("custom_dropstitch.record_custom_route")
            self.route_id = route_obj.id if len(route_obj) else False
        else:
            name = super()._get_sale_order_line_multiline_description_variants()
        return name

    def get_description_following_lines(self):
        name_line = [self.name.splitlines()[0]]
        if self.custom_line1:
            name_line.append("line 1: " + self.custom_line1 or "")
        if self.custom_line2:
            name_line.append("line 2: " + self.custom_line2 or "")
        if self.custom_line3:
            name_line.append("line 3: " + self.custom_line3 or "")
        if self.custom_initials:
            name_line.append("Initials : " + self.custom_initials or "")
        if self.custom_personalize:
            name_line.append("Personalize : " + self.custom_personalize or "")
        return name_line

    @api.depends(
        "product_id",
        "custom_line1",
        "custom_line2",
        "custom_line3",
        "custom_personalize",
        "custom_initials",
    )
    def _compute_name(self):
        super()._compute_name()

    @api.depends(
        "qty_invoiced",
        "qty_delivered",
        "qty_to_intent",
        "product_uom_qty",
        "state",
        "order_id.state",
        "order_id.custom_policy",
    )
    def _compute_qty_to_invoice(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """
        for line in self:
            if line.state == "sale" and not line.display_type:
                if line.order_id.custom_policy == "products":
                    if line.product_id.invoice_policy == "order":
                        line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                    else:
                        line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
                elif line.order_id.custom_policy == "order":
                    line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                elif line.order_id.custom_policy == "delivery":
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
                elif line.order_id.custom_policy == "intent":
                    if line.is_delivery:
                        line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                    else:
                        line.qty_to_invoice = line.qty_to_intent
            else:
                line.qty_to_invoice = 0

    @api.depends(
        "move_ids.state",
        "move_ids.scrapped",
        "move_ids.quantity",
        "move_ids.product_uom",
    )
    def _compute_qty_to_intent(self):
        for line in self:
            if line.qty_delivered_method == "stock_move":
                qty = 0.0
                outgoing_moves, incoming_moves = line._get_outgoing_incoming_moves()
                for move in outgoing_moves:
                    if move.state != "done":
                        qty += move.product_uom._compute_quantity(
                            move.quantity, line.product_uom, rounding_method="HALF-UP"
                        )
                line.qty_to_intent = qty

    def create(self,vals):
        results = super().create(vals)
        for res in results:
            if res.order_id.website_id:
                res._onchange_custom_product_no_variant_attribute_value_ids()
        return results

    def get_yarn_component_images(self):
        yarn_component_images = ''
        if not self:
            return yarn_component_images
        
        combination = self.product_no_variant_attribute_value_ids.ids or [] 
        if combination:
            yarn_attrib_ids = (self.env["product.template.attribute.value"].sudo()
                .browse(combination)
                .filtered(lambda a: a.attribute_id.show_yarn_component_image))
            if not yarn_attrib_ids:
                return ''
            
            yarn_component_ids = [[
                    i.product_attribute_value_id.custom_product_component.id,
                    i.product_attribute_value_id.custom_product_component.display_name,
                ]for i in yarn_attrib_ids]

            yarn_component_images = self.env["ir.ui.view"]._render_template(
                "custom_dropstitch.yarn_compoentn_images", values={"yarn_components": yarn_component_ids},
            )
        return yarn_component_images
