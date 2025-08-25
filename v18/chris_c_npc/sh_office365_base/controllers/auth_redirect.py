# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

import werkzeug
import werkzeug.utils
from odoo import http, _
from odoo.http import request
from odoo.exceptions import UserError


class Redirects(http.Controller):

    @http.route("/sh_office365_base/redirect", auth="public")
    def get_code(self, **kwargs):
        if kwargs.get('code'):
            # code = kwargs.get('code')
            # rec_id = kwargs.get('state')
            # rec_id_int = int(kwargs.get('state'))
            config = request.env['sh.office365.base.config'].search([
                ('id', '=', int(kwargs.get('state')))], limit=1)
            if config:
                # config.write({'code' : code})
                config.generate_token(kwargs['code'])
            return werkzeug.utils.redirect("/")
        else:
            raise UserError(_("Could not receive code, check credentials"))
