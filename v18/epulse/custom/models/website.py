from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo.http import request
from odoo import models, http
import base64
from datetime import timedelta
from odoo import SUPERUSER_ID, api, fields, models, tools

class Website(models.Model):
    _inherit = "website"

    def sale_get_order(self, force_create=False):
        """ Return the current sales order after mofifications specified by params.

        :param bool force_create: Create sales order if not already existing

        :returns: current cart, as a sudoed `sale.order` recordset (might be empty)
        """
        self.ensure_one()
        print("overriten function")
        self = self.with_company(self.company_id)
        SaleOrder = self.env['sale.order'].sudo()

        sale_order_id = request.session.get('sale_order_id')

        if sale_order_id:
            sale_order_sudo = SaleOrder.browse(sale_order_id).exists()
            # CUSTOM: Ignore existing order if is_online is True, force new order creation
            if sale_order_sudo and sale_order_sudo.is_online:
                sale_order_sudo = SaleOrder
        elif not request.session.get('sale_order_id') and force_create:
            print("Printinggggg")
            sale_order_sudo = SaleOrder
        elif self.env.user and not self.env.user._is_public():
            sale_order_sudo = self.env.user.partner_id.last_website_so_id
            if sale_order_sudo:
                # CUSTOM: Ignore last order if is_online is True, force new order creation
                if sale_order_sudo.is_online:
                    sale_order_sudo = SaleOrder
                else:
                    available_pricelists = self.get_pricelist_available()
                    so_pricelist_sudo = sale_order_sudo.pricelist_id
                    if so_pricelist_sudo and so_pricelist_sudo not in available_pricelists:
                        # Do not reload the cart of this user last visit
                        # if the cart uses a pricelist no longer available.
                        sale_order_sudo = SaleOrder
                    else:
                        # Do not reload the cart of this user last visit
                        # if the Fiscal Position has changed.
                        fpos = sale_order_sudo.env['account.fiscal.position'].with_company(
                            sale_order_sudo.company_id
                        )._get_fiscal_position(
                            sale_order_sudo.partner_id,
                            delivery=sale_order_sudo.partner_shipping_id
                        )
                        if fpos.id != sale_order_sudo.fiscal_position_id.id:
                            sale_order_sudo = SaleOrder
        else:
            sale_order_sudo = SaleOrder

        # Ignore the current order if a payment has been initiated. We don't want to retrieve the
        # cart and allow the user to update it when the payment is about to confirm it.
        if sale_order_sudo and sale_order_sudo.get_portal_last_transaction().state in (
                'pending', 'authorized', 'done'
        ):
            sale_order_sudo = None

        if not (sale_order_sudo or force_create):
            # Do not create a SO record unless needed
            if request.session.get('sale_order_id'):
                request.session.pop('sale_order_id')
                request.session.pop('website_sale_cart_quantity', None)
            return self.env['sale.order']

        partner_sudo = self.env.user.partner_id

        # cart creation was requested
        if not sale_order_sudo:
            so_data = self._prepare_sale_order_values(partner_sudo)
            sale_order_sudo = SaleOrder.with_user(SUPERUSER_ID).create(so_data)

            request.session['sale_order_id'] = sale_order_sudo.id
            request.session['website_sale_cart_quantity'] = sale_order_sudo.cart_quantity
            # The order was created with SUPERUSER_ID, revert back to request user.
            return sale_order_sudo.with_user(self.env.user).sudo()

        # Existing Cart:
        #   * For logged user
        #   * In session, for specified partner

        # case when user emptied the cart
        if not request.session.get('sale_order_id'):
            request.session['sale_order_id'] = sale_order_sudo.id
            request.session['website_sale_cart_quantity'] = sale_order_sudo.cart_quantity

        # check for change of partner_id ie after signup
        if partner_sudo.id not in (sale_order_sudo.partner_id.id, self.partner_id.id):
            sale_order_sudo._update_address(partner_sudo.id, ['partner_id'])

        return sale_order_sudo