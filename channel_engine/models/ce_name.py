# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ChannelName(models.Model):
    _name = 'ce.name'
    _description = "Channel Name"

    name = fields.Char('Channel Name', help="Channel Name")
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position',
                                         help="Fiscal position to be used for this channel.")
    channel_id = fields.Char("Channel ID", help="Channel Engine Channel ID")
    is_enabled_channel = fields.Boolean("Is Enabled in CE?", default=False, help="Channel is Enabled/Disabled in CE")
    instance_id = fields.Many2one("ce.instance", string="Channel Instance", help="Select channel engine instance")
    
    @api.constrains('name')
    def _identify_same_channel_name(self):
        for record in self:
            obj = self.search([('name', '=ilike', record.name), ('id', '!=', record.id)])
            if obj:
                raise UserError("There is another channel name with the same name: %s" % record.name)                
