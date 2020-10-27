# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = "Product Brand"
    
    name =  fields.Char("Brand Name", required=True, copy=False, help="Brand Name")
    