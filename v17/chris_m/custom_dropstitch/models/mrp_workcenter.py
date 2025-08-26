# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

import logging

_logger = logging.getLogger(__name__)

sel_custom_machine_no = [
    ("na", "N/A"),
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("4", "4"),
    ("5", "5"),
    ("6", "6"),
    ("7", "7"),
    ("8", "8"),
    ("9", "9"),
    ("10", "10"),
    ("11", "11"),
    ("12", "12"),
    ("13", "13"),
    ("14", "14"),
    ("15", "15"),
    ("16", "16"),
    ("17", "17"),
    ("18", "18"),
    ("19", "19"),
    ("20", "20"),
    ("21", "21"),
]


class CustomMrpWorkCenter(models.Model):
    _inherit = "mrp.workcenter"

    custom_machine_no = fields.Selection(sel_custom_machine_no, string="Machine No")
