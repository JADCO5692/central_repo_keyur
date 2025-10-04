# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta

import logging

_logger = logging.getLogger(__name__)

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

sel_shipping_fees = [
    ("charge_fees", "Charge Shipping Fees"),
    ("no_fees", "No Shipment Fees"),
]

sel_custom_check_import = [
    ("na", "N/A"),
    ("i2g", "I2g"),
    ("size", "Check Size(Baublebar)"),
    ("design", "Check Design(Butterscoth)"),
]


class CustomResPartner(models.Model):
    _inherit = "res.partner"
    _description = "Update Customer info"

    # Package NOtes
    custom_label_template_id = fields.Many2one(
        comodel_name="custom.label.template", string="Packaging Notes Template"
    )
    custom_label_type = fields.Selection(
        sel_custom_label_type, string="Label Type", tracking=True
    )
    custom_label_placement = fields.Selection(
        sel_custom_label_placement, string="Label Placement", tracking=True
    )
    custom_shipping_fees = fields.Selection(
        sel_shipping_fees, string="Shipping Fees", default="charge_fees", tracking=True
    )
    custom_bag_info = fields.Selection(
        sel_custom_bag_info, string="Bag Info", tracking=True
    )
    custom_box_info = fields.Selection(
        sel_custom_box_info, string="Box Info", tracking=True
    )

    custom_brand_label = fields.Integer("Brand Label", tracking=True)
    custom_care_label = fields.Integer("Care Label", tracking=True)

    custom_instruction = fields.Char(
        "Label Special Instruction", size=80, tracking=True
    )
    custom_pack_instr = fields.Char("Packaging Instruction", size=80, tracking=True)

    custom_label_image = fields.Binary(string="Label Image")

    custom_dropship_order = fields.Boolean(
        string="Dropship",
        tracking=True,
    )
    custom_require_payment = fields.Boolean(
        string="Online payment",
        help="Request a online payment from the customer to confirm the order.",
        default=True,
        tracking=True,
    )
    custom_prepayment_percent = fields.Float(
        string="Prepayment percentage",
        help="The percentage of the amount needed that must be paid by the customer to confirm the order.",
        default=0.5,
        tracking=True,
    )

    custom_receipt_type_id = fields.Many2one(
        comodel_name="stock.picking.type", string="Receipt: Picking Type", tracking=True
    )

    custom_allowed_customer_ids = fields.Many2many(
        "res.partner",
        "res_partner_allowed_customer_rel",
        "partner_id",
        "allowed_customer_id",
        string="Allowed Customers",
        domain=[("customer_rank", ">", 0)],
    )

    custom_allowed_supplier_ids = fields.Many2many(
        "res.partner",
        "res_partner_allowed_supplier_rel",
        "partner_id",
        "allowed_supplier_id",
        string="Allowed Supplier",
        domain=[("supplier_rank", ">", 0)],
    )

    custom_policy = fields.Selection(
        [
            ("products", "Based on Products"),
            ("order", "Based on Order Quantity"),
            ("delivery", "Based on Delivered Quantity"),
            ("intent", "Based on Intent"),
        ],
        default="intent",
        string="Invoicing Policy",
        tracking=True,
    )
    custom_auto_pay_limit = fields.Float(
        string="Auto Payment Limit", default=1000, tracking=True
    )
    shopify_instance_id = fields.Many2one("shopify.instance.ept", "Shopify Instance")

    custom_generate_type = fields.Selection(
        [("mass_import", "Mass Import"),
         ("biquette_boutique", "Biquette Boutique"),
         ("biquette_retail", "Biquette Retail"),
         ("mkc_generated", "MKC Generated"),
         ("pmc_generated", "PMC Generated")],
        string="Customer Generation Type",
        default="mkc_generated",
        tracking=True,
    )
    custom_customer_logo = fields.Binary(string="Customer Logo")

    # Mass Import
    custom_sale_order_template_id = fields.Binary(string="Import Template")
    custom_sale_order_template_name = fields.Char(string="Template Name")
    custom_sale_order_template_flag = fields.Boolean(string="Import Flag")
    custom_mass_imp_val = fields.Selection(
        sel_custom_check_import,
        string="Mass Import Validation",
        copy=True,
        default="na",
        tracking=True,
    )
    custom_mass_imp_colorway = fields.Many2one(
        comodel_name="product.attribute",
        string="Mass Import Colorway",
        copy=True,
        tracking=True,
    )
    custom_capture_tiff_file = fields.Boolean(
        string="Capture TIFF File", default=True, tracking=True
    )
    custom_capture_image = fields.Boolean(
        string="Capture Image", default=True, tracking=True
    )
    
    allow_partial_payment = fields.Boolean(string="Down-Payment", default=True, tracking=True)
    
    custom_allowed_shipping_ids = fields.Many2many(
        "delivery.carrier",
        "delivery_carrier_allowed_customer_rel",
        "partner_id",
        "allowed_shipping_id",
        string="Allowed Deliveries",
    )

    custom_order_confirmation_ids = fields.Many2many(
        "res.partner",
        "res_partner_order_confirmation_rel",
        "partner_id",
        "contact_id",
        string="Order Confirmation",
    )

    custom_shipping_confirmation_ids = fields.Many2many(
        "res.partner",
        "res_partner_shipping_confirmation_rel",
        "partner_id",
        "contact_id",
        string="Shipping Confirmation",
    )

    custom_invoice_generated_ids = fields.Many2many(
        "res.partner",
        "res_partner_invoice_generated_rel",
        "partner_id",
        "contact_id",
        string="Invoice is Generated",
    )

    custom_payment_completed_ids = fields.Many2many(
        "res.partner",
        "res_partner_payment_completed_rel",
        "partner_id",
        "contact_id",
        string="Payment is completed",
    )

    custom_property_expense_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Account Expense",
        domain=[("deprecated", "=", False), ("account_type", "=", "expense")],
        help="This account will be used for the expenses of this partner.",
        tracking=True,
    )
    
    shipstation_store_id = fields.Many2one('shipstation.store.ept', string='Shipstation Store', copy=False)

    prevent_intrimed_entries = fields.Boolean(
        string="Prevent Intrimed Entries",
        help="If checked, Accounting entries for the stock output account and expense will not be generated for such moves",
        default=False,
    )
    custom_so_special_inst = fields.Html("Customer Special Instruction", copy=False)
    is_show_gift_msg = fields.Boolean("Show Gift Message in Delivery")

    @api.onchange("custom_label_template_id")
    def _onchange_custom_label_template(self):
        if self.custom_label_template_id:
            template = self.custom_label_template_id
            self.custom_label_type = template.label_type
            self.custom_label_placement = template.label_placement
            self.custom_bag_info = template.bag_info
            self.custom_box_info = template.box_info
            self.custom_brand_label = template.brand_label
            self.custom_care_label = template.care_label
            self.custom_instruction = template.instruction
            self.custom_pack_instr = template.pack_instr
            self.custom_label_image = template.label_image
    
    @api.onchange("custom_prepayment_percent")
    def _onchange_custom_prepayment_percent(self):
        if self.custom_prepayment_percent:
            self.adv_payment_amount = (self.custom_prepayment_percent * 100)

    @api.onchange("custom_sale_order_template_id")
    def _onchange_custom_sale_order_template_id(self):
        if self.custom_sale_order_template_id:
            self.custom_sale_order_template_flag = True
        else:
            self.custom_sale_order_template_flag = False

    def custom_archive_contacts_cron(self, days_ago, days_ago_biq=180):
        date_days_ago = datetime.today() - timedelta(days=days_ago)
        date_days_ago_biq = datetime.today() - timedelta(days=days_ago_biq)

        contacts_to_archive = self.search(
            [
                ("custom_generate_type", "=", "mass_import"),
                ("create_date", "<", date_days_ago),
            ]
        )
        contacts_to_archive.write({"active": False})
        
        contacts_to_archive = self.search(
            [
                ("custom_generate_type", "=", "biquette_retail"),
                ("create_date", "<", date_days_ago_biq),
            ]
        )
        contacts_to_archive.write({"active": False})

    def _get_complete_name(self):
        res = super(CustomResPartner,self)._get_complete_name()
        if self.type == 'delivery':
            split_name = res.split(',') if res else []
            if len(split_name) > 1:
                res = split_name[1].strip() or ''
        return res
    
    @api.model
    def _commercial_fields(self):
        res = super(CustomResPartner,self)._commercial_fields()
        addtional_fields = [
            'team_id',
            'user_id',
            'property_payment_term_id',
            'property_product_pricelist',
            'property_delivery_carrier_id',
            'custom_dropship_order',
            'custom_capture_tiff_file',
            'custom_capture_image',
            'custom_shipping_fees',
            'custom_customer_logo',
            'custom_auto_pay_limit',
            'custom_label_type',
            'custom_label_placement',
            'custom_bag_info',
            'custom_box_info',
            'custom_brand_label',
            'custom_care_label',
            'custom_instruction',
            'custom_pack_instr',
            'custom_label_image',
            'custom_require_payment',
            'custom_prepayment_percent',
            'min_order_amount',
            'adv_payment_amount',
            'min_payment_term',
            'max_partial_order',
            'custom_allowed_shipping_ids',
            'prevent_intrimed_entries',
            'custom_so_special_inst',
            'custom_allowed_customer_ids',
        ]
        
        res = res + addtional_fields
        return res

    def _get_notify_partner_ids(self, field_name, object):
        """
        Returns the partner ids to notify based on the field name.
        """
        partners = self[field_name]
        if not partners:
            partners = self.parent_id[field_name]
        if hasattr(object, 'shopify_instance_id') and not object.shopify_instance_id and not partners:
            return []
        else:
            return partners.ids if partners else self.ids