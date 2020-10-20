# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.depends('image_1920')
    def get_product_main_image_link(self):
        for i in self:
            if i._name == 'product.product':
                main_image_id = i.env['product.main.image.link'].search([('product_id', '=', i.id)])
                if main_image_id:
                    main_image_id.unlink()
                    i.main_image_id = i.env['product.main.image.link'].create(
                        {'product_id': i.id, 'image': i.image_1920}).id
                else:
                    i.main_image_id = i.env['product.main.image.link'].create(
                        {'product_id': i.id, 'image': i.image_1920}).id

    main_image_id = fields.Many2one('product.main.image.link', string="Main Image", compute="get_product_main_image_link", store=True)
    main_image_url = fields.Char('Image URL', compute="compute_main_image_url")

    @api.depends('main_image_id', 'main_image_id.image_url')
    def compute_main_image_url(self):
        for product in self:
            product.main_image_url = product.main_image_id.image_url


class ProductMainImageLink(models.Model):
    _name = 'product.main.image.link'
    _description = "Product Main Image Link"

    image = fields.Binary(string='Image')
    product_id = fields.Many2one('product.product', string='Product')
    image_url = fields.Char('Image URL', help='Product Image URL')

    @api.model_create_multi
    def create(self, vals):
        image_id = super(ProductMainImageLink, self).create(vals)
        base_path = self.env['ir.config_parameter'].sudo().get_param('web.base.url') + "/web"
        sub_path = "/image/product.main.image.link/%s/image/%s" % (image_id.id, "image")
        image_id.write({'image_url': base_path + sub_path})
        return image_id

    def write(self, vals):
        base_path = self.env['ir.config_parameter'].sudo().get_param('web.base.url') + "/web"
        sub_path = "/image/product.main.image.link/%s/image/%s" % (self.id, "image")
        vals.update({'image_url': base_path + sub_path})
        return super(ProductMainImageLink, self).write(vals)


class ProductImage(models.Model):
    _inherit = 'product.image'

    product_image_full_name = fields.Char(string="Product Image Name", help="Product image name.")
    image_url = fields.Char('Image URL', help='Product Image URL')

    @api.model_create_multi
    def create(self, vals):
        image_id = super(ProductImage, self).create(vals)
        base_path = self.env['ir.config_parameter'].sudo().get_param('web.base.url') + "/web"
        sub_path = "/image/product.image/%s/image/%s" % (image_id.id, image_id.product_image_full_name)
        image_id.write({'image_url': base_path + sub_path})
        return image_id

    def write(self, vals):
        base_path = self.env['ir.config_parameter'].sudo().get_param('web.base.url') + "/web"
        sub_path = "/image/product.image/%s/image/%s" % (
        self.id, vals.get('product_image_full_name', self.product_image_full_name))
        vals.update({'image_url': base_path + sub_path})
        return super(ProductImage, self).write(vals)
