from odoo import models, fields, api, _
import re

map_list = [
    ['product.template,name', 'channel.product.product,name'],
    ['product.template,description_sale', 'channel.product.product,description']
]


class Products(models.Model):
    _inherit = 'channel.product.product'

    def map_translations(self):
        translation = self.env['ir.translation']
        for item in map_list:
            src = translation.search([('name','=', item[0]), ('res_id','=',self.product_id.product_tmpl_id.id)])
            if src:
                des = translation.search([('name', '=', item[1]), ('res_id', '=', self.id)])
                des.unlink()
                for s in src:
                    s.copy(default={'name': item[1], 'res_id': self.id})

    def cleanhtml(self, raw_html):
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext

    def get_translated_data(self):
        translated_data = []
        translation = self.env['ir.translation']
        for item in map_list:
            src = translation.search([('name', '=', item[1]), ('res_id', '=', self.id)])
            for rec in src:
                translated_data.append({"key": (item[1].split(',')[-1]) + ' - ' + rec.lang, "Value": rec.value or '', "Type": "TEXT", "IsPublic": True})
            if src:
                value = src[0].src and self.cleanhtml(src[0].src) or ''
                translated_data.append({"key": (item[1].split(',')[-1]) + ' - EN_us', "Value": value, "Type": "TEXT", "IsPublic": True})
        return translated_data
