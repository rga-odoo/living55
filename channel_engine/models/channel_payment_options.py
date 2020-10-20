# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ChannelPaymentOptions(models.Model):
    _name = "channel.payment.options"
    _description = "Channel Payment Options"
    _order = 'id desc'

    name = fields.Char("Payment Method", required=True, help="Channel payment method name.")
    instance_id = fields.Many2one('ce.instance', string='Instance Name', help="Instance name")
