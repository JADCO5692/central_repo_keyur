from odoo import models, fields

sel_custom_label_type = [
    ("na", "N/A"),
    ("cust_label", "Customer Label"),
    ("biquette_label", "Biquette Label"),
    ("no_label", "No Label"),
    ("alc_cust_label", "Alcantara Customer Label"),
]

sel_custom_bag_info = [
    ("plastic_bag", "Plastic Bag"),
    ("no_bag", "No Bag"),
    ("cust_bag", "Customer Brand Bag"),
    ("biquette_bag", "Biquette bag"),
    ("mineola_bag", "Mineola Bag"),
]

sel_custom_label_placement = [
    ("na", "N/A"),
    ("front_right", "Front Right (Low)"),
    ("front_left", "Front left (Low)"),
    ("back_right", "Back Right (Low)"),
    ("back_left", "Back Left (Low)"),
    ("back_left_top", "Back Left (Top)"),
    ("fold_right_low", "Fold Around (Right Low)"),
]

sel_custom_box_info = [("one_unit_box", "1 Unit Box"), ("bulk", "Bulk Box")]


class CustomLabelTemplate(models.Model):
    _name = "custom.label.template"
    _description = "Custom Label Template"

    name = fields.Char(string="Label Template Name", required=True)
    label_type = fields.Selection(sel_custom_label_type, string="Label Type")
    label_placement = fields.Selection(
        sel_custom_label_placement, string="Label Placement"
    )
    bag_info = fields.Selection(sel_custom_bag_info, string="Bag Info")
    box_info = fields.Selection(sel_custom_box_info, string="Box Info")
    brand_label = fields.Integer(string="Brand Label")
    care_label = fields.Integer(string="Care Label")
    instruction = fields.Char(string="Label Special Instruction", size=80)
    pack_instr = fields.Char(string="Packaging Instruction", size=80)
    label_image = fields.Binary(string="Label Image")
