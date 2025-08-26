# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ShopifyResPartnerEpt(models.Model):
    _inherit = "shopify.res.partner.ept"
    _description = "Shopify Res Partner"

    @api.model
    def shopify_create_contact_partner(self, vals, instance, queue_line):
        partner = super(ShopifyResPartnerEpt, self).shopify_create_contact_partner(
            vals, instance, queue_line
        )
        if instance.custom_label_template_id and partner:
            self._update_partner_from_shopify_order(partner, instance)
        return partner

    def _update_partner_from_shopify_order(self, partner, instance):
        if not partner.custom_label_type:
            partner_vals = {
                "custom_label_type": instance.custom_label_template_id.label_type,
                "custom_label_placement": instance.custom_label_template_id.label_placement,
                "custom_bag_info": instance.custom_label_template_id.bag_info,
                "custom_box_info": instance.custom_label_template_id.box_info,
                "custom_brand_label": instance.custom_label_template_id.brand_label,
                "custom_care_label": instance.custom_label_template_id.care_label,
                "custom_instruction": instance.custom_label_template_id.instruction,
                "custom_pack_instr": instance.custom_label_template_id.pack_instr,
                "custom_label_image": instance.custom_label_template_id.label_image,
                "customer_rank": 0,
                "shopify_instance_id": instance.id,
                "custom_generate_type": "biquette_retail",
                "property_payment_term_id": self.env.ref("account.account_payment_term_immediate").id,
                "custom_prepayment_percent": 1,
            }
            partner.write(partner_vals)
