# -*- encoding: utf-8 -*-
from odoo import models, fields


class ProductBrand(models.Model):
    _name = 'channel.product.brand'
    _description = "Channel Product Brand"

    name = fields.Char('Brand Name', help="Product brand name.")
    brand_logo = fields.Binary('Brand Logo',help="Product brand Logo(Image).")
    partner_id = fields.Many2one('res.partner', string='Partner Name',
                                 help='Select a partner for this brand if it exists.',
                                 ondelete='restrict')