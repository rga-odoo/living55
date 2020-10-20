import base64, requests
from odoo import models, fields,api,_
from odoo.exceptions import Warning


class CEProductImages(models.Model):
    _name = "ce.product.images"
    _description = "CE Product Images"
        
    image_name = fields.Char(string="Image Name", help="Product image name")
    product_image = fields.Binary(string="Product Image", attachment=True)
    product_image_full_name = fields.Char(string="Product Image Name", help="CE product image full name.")
    ce_product_variant_id = fields.Many2one("channel.product.product")
    ce_image_url = fields.Char(string="Image URL", help="CE product image URL")

    @api.model
    def create(self, vals):
        image_id = super(CEProductImages, self).create(vals)
        base_path = self.env['ir.config_parameter'].get_param('web.base.url')
        sub_path = "/image/ce.product.images/%s/product_image/%s" % (image_id.id, image_id.product_image_full_name)
        image_id.write({'ce_image_url': base_path + sub_path})
        return image_id

    def write(self, vals):
        base_path = self.env['ir.config_parameter'].get_param('web.base.url')
        sub_path = "/image/ce.product.images/%s/product_image/%s" % (self.id, vals.get('product_image_full_name',self.product_image_full_name))
        vals.update({'ce_image_url': base_path + sub_path})
        return super(CEProductImages, self).write(vals)