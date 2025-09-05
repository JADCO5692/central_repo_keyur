# -*- coding: utf-8 -*-
##################################################################################
#
#    Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
#################################################################################

def pre_init_check(cr):
    from odoo.release import series
    from odoo.exceptions import ValidationError

    if series != '18.0':
        raise ValidationError('Module support Odoo series 18.0 found {}.'.format(series))
