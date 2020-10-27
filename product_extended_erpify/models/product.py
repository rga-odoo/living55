# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    # related to display product product information if is_product_variant
    barcode_inner = fields.Char('Barcode Inner', compute='_compute_barcode_inner', inverse='_set_barcode_inner', search='_search_barcode_inner')
    barcode_master = fields.Char('Barcode Master', compute='_compute_barcode_master', inverse='_set_barcode_master', search='_search_barcode_master')
    brand_id = fields.Many2one("product.brand", "Product Brand", copy=False)
    box_ecom = fields.Many2one("product.packaging", "Ecommerce box", help="Ecommerce box", copy=False) 
    product_range = fields.Integer("Assortiment", copy=False)
    
    # Barcode Inner
    @api.depends('product_variant_ids.barcode_inner')
    def _compute_barcode_inner(self):
        self.barcode_inner = False
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.barcode_inner = template.product_variant_ids.barcode_inner

    def _search_barcode_inner(self, operator, value):
        templates = self.with_context(active_test=False).search([('product_variant_ids.barcode_inner', operator, value)])
        return [('id', 'in', templates.ids)]

    def _set_barcode_inner(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.barcode_inner = self.barcode_inner
            
    # Barcode Master       
    @api.depends('product_variant_ids.barcode_master')
    def _compute_barcode_master(self):
        self.barcode_master = False
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.barcode_master = template.product_variant_ids.barcode_master

    def _search_barcode_master(self, operator, value):
        templates = self.with_context(active_test=False).search([('product_variant_ids.barcode_master', operator, value)])
        return [('id', 'in', templates.ids)]

    def _set_barcode_master(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.barcode_master = self.barcode_master


class ProductProduct(models.Model):
    _inherit = "product.product"
    
    barcode_inner = fields.Char('Barcode Inner', copy=False)
    barcode_master = fields.Char('Barcode Master', copy=False)
    brand_id = fields.Many2one("product.brand", "Product Brand", related="product_tmpl_id.brand_id", readonly=False, store=True, copy=False)
    box_ecom = fields.Many2one("product.packaging", "Ecommerce box", related="product_tmpl_id.box_ecom", readonly=False, store=True, copy=False, help="Ecommerce box")
    product_range = fields.Integer("Assortiment", related="product_tmpl_id.product_range", readonly=False, store=True, copy=False) 