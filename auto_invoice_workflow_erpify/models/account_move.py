from odoo import models, fields, api, _
from odoo.osv.osv import except_osv
from odoo.exceptions import Warning
import pytz


class global_channel(models.Model):
    _inherit = "account.move"
    
    global_channel_id=fields.Many2one('global.channel.ept', string='Global Channel')
