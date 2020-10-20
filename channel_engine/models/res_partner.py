# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    channel_customer_no = fields.Char('Customer No', size=50, help="Channel Customer Number")
