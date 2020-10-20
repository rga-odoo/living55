# -*- coding: utf-8 -*-
import json, requests
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.channel_engine.channel_engine_api.api import ChannelEngine


class ChannelProductProduct(models.Model):
    _name = "channel.product.product"
    _description = "Channel Product"

    name = fields.Char('Product Name', size=256, required=True, translate=True)
    instance_id = fields.Many2one('ce.instance', string='Instance', required=True)
    merchant_product_no = fields.Char("Merchant Product No", size=64, required=True,
                                      help="A unique identifier of the product.")
    product_id = fields.Many2one('product.product', 'Odoo Product ID', required=True)
    channel_product_tmpl_id = fields.Many2one("channel.product.template", "CE Product Template", required=True,
                                              ondelete="cascade")
    description = fields.Html("Product Description", translate=True, sanitize=False)
    purchase_price = fields.Float("Purchase Price", help="Product purchase price.")
    shipping_cost = fields.Float("Shipping Cost", help="Product shipping cost.")
    msrp = fields.Float("MSRP", help="Manufacturer's suggested retail price.")
    shipping_time = fields.Char("Shipping Time",
                                help="A textual representation of the shipping time. For example, in Dutch: 'Ordered before 22:00 on working days, tomorrow at home'")
    image_url = fields.Char("Image URL", help="A URL at which an image of this product can be found.")
    category_trail = fields.Char("Category Trail",
                                 help="The category to which this product belongs. Please supply this field in the following format: 'maincategory &gt; category &gt; subcategory' For example: 'vehicles &gt; bikes &gt; mountainbike'")
    exported_in_channel = fields.Boolean("Exported Product To Channel ?", default=False)
    ean13 = fields.Char(related="product_id.barcode", string="Barcode / EAN", store=False, readonly=True,
                        help="Product Barcode / EAN")
    product_price = fields.Float("Product Price", help="Product Price")
    size = fields.Char("Size", help="Product Size")
    color = fields.Char("Color", help="Product Color")
    stock = fields.Char("Stock", help="Product Stock")
    channel_stock_type = fields.Selection([('fix', 'Fix'), ('percentage', 'Percentage')], string='Fix Stock Type')
    channel_stock_value = fields.Float(string='Fix Stock Value')
    channel_product_no = fields.Char("Channel Product No", size=50, help="Channel product number.")
    is_active_in_channel = fields.Boolean(string="Is Active In Channel ?",
                                          help="This product is active in channel engine for sale.")
    ce_product_image_ids = fields.One2many("ce.product.images", "ce_product_variant_id", string="Product images")

    @api.constrains('ce_product_image_ids')
    def check_no_of_image_validation(self):
        if len(self.ce_product_image_ids) > 10:
            raise UserError(
                "You can not Create more than 10 image becuase channel engine provide only 10 image set in product.")

    def get_description(self):
        if self.instance_id.prod_description_erpify:
            return self.product_id[self.instance_id.prod_description_erpify.name] or ''
        else:
            return self.product_id.sale_description

    def get_title(self):
        if self.instance_id.prod_title_erpify:
            return self.product_id[self.instance_id.prod_title_erpify.name] or ''
        else:
            return self.product_id.name

    def get_channel_product_stock(self, channel_product, warehouse_id, stock_type='virtual_available'):
        context = dict(self._context) or {}
        actual_stock = 0.0
        product = self.env['product.product'].with_context(warehouse_id=warehouse_id).browse(
            channel_product.product_id.id)
        if hasattr(channel_product.product_id, str(stock_type)):
            actual_stock = getattr(channel_product.product_id, stock_type)
        else:
            actual_stock = product.qty_available

        minimum_stock = []
        is_mrp_installed = self.sudo().env['ir.module.module'].search([('name', '=', 'mrp'), ('state', '=', 'installed')])
        if is_mrp_installed:
            bom_product = self.env['mrp.bom'].sudo()._bom_find(product=product)
        else:
            bom_product = False
        if bom_product:
            bom_product_line_ids = self.get_bom_product_component_lines(product, quantity=1)
            for bom_line, line in bom_product_line_ids:
                bom_comp_product_stock = getattr(bom_line.product_id, stock_type) if hasattr(bom_line.product_id, str(
                    stock_type)) else bom_line.product_id.qty_available
                actual_stock = int(bom_comp_product_stock / bom_line.product_qty)
                minimum_stock.append(actual_stock)
            actual_stock = minimum_stock and min(minimum_stock) or 0

        if actual_stock >= 1.00:
            if channel_product.channel_stock_type == 'fix':
                if channel_product.channel_stock_value >= actual_stock:
                    return actual_stock
                else:
                    return channel_product.channel_stock_value

            elif channel_product.channel_stock_type == 'percentage':
                quantity = int(actual_stock * channel_product.channel_stock_value)
                if quantity >= actual_stock:
                    return actual_stock
                else:
                    return quantity
        return actual_stock

    @api.model
    def get_bom_product_component_lines(self, product, quantity):
        try:
            bom_obj = self.env['mrp.bom']
            bom_point = bom_obj.sudo()._bom_find(product=product)
            from_uom = product.uom_id
            to_uom = bom_point.product_uom_id
            factor = from_uom._compute_quantity(quantity, to_uom) / bom_point.product_qty
            bom, lines = bom_point.explode(product, factor, picking_type=bom_point.picking_type_id)
            return lines
        except BaseException:
            return []

    def update_product_stock_in_channel(self, instance, channel_products=False):
        if not channel_products:
            channel_products = self.search([('instance_id', '=', instance.id), ('exported_in_channel', '=', True)])
        if not channel_products:
            return True

        channel_log_book_obj = self.env['channel.log.book']
        channel_log_book_line_obj = self.env['channel.log.book.line']
        channel_engine_obj = ChannelEngine()
        # location_id = instance.warehouse_id and instance.warehouse_id.lot_stock_id and instance.warehouse_id.lot_stock_id.id
        warehouse_id = instance.warehouse_id and instance.warehouse_id.id
        product_stock = 0
        job = False
        results = {}
        for product_counter, channel_product in enumerate(channel_products, 1):
            if not channel_product.channel_product_tmpl_id.exported_in_channel:
                continue

            merchant_prod_no = channel_product.merchant_product_no or channel_product.product_id.default_code
            if instance.stock_field:
                product_stock = self.get_channel_product_stock(channel_product, warehouse_id, instance.stock_field.name)
            else:
                product_stock = self.get_channel_product_stock(channel_product, warehouse_id)

            product_data = [{
                "MerchantProductNo": str(merchant_prod_no),
                "Stock": int(product_stock) if (int(product_stock) > 0) else 0
            }]
            try:
                results = channel_engine_obj.get_channel_offer_api_object(instance, data=product_data) or {}
            except Exception as e:
                if not job:
                    value = {
                        'instance_id': instance.id,
                        'message': 'Update Product Price In Channel Engine.',
                        'application': 'update_product_price',
                        'operation_type': 'export',
                        'skip_process': True
                    }
                    job = channel_log_book_obj.create(value)
                job_line_val = {
                    'record_id': int(product_counter),
                    'job_id': job.id,
                    'log_type': 'error',
                    'action_type': 'skip_line',
                    'operation_type': 'export',
                    'message': 'Exception when calling OfferApi->offer_stock_price_update: %s\n' % (e),
                }
                channel_log_book_line_obj.create(job_line_val)
            if results:
                resp_success = results.get('Success', False)
                resp_content = results.get('Content', {})
                resp_content_product = resp_content.get(str(channel_product.name), '')
                if not resp_success or resp_content_product:
                    if not job:
                        value = {
                            'instance_id': instance.id,
                            'message': '%s' % (str(results.get('Message'))),
                            'application': 'update_product_stock',
                            'operation_type': 'export',
                            'skip_process': True
                        }
                        job = channel_log_book_obj.create(value)
                    job_line_val = {
                        'record_id': int(product_counter),
                        'channel_order_ref': channel_product.name,
                        'job_id': job.id,
                        'log_type': 'error',
                        'action_type': 'skip_line',
                        'operation_type': 'export',
                        'message': '%s' % (str(resp_content)),
                    }
                    channel_log_book_line_obj.create(job_line_val)
        return True


    def update_product_price_in_channel(self, instance, channel_products=False):
        if not channel_products:
            channel_products = self.search([('instance_id', '=', instance.id), ('exported_in_channel', '=', True)])
        if not channel_products:
            return True

        channel_log_book_obj = self.env['channel.log.book']
        channel_log_book_line_obj = self.env['channel.log.book.line']
        channel_engine_obj = ChannelEngine()
        results = False
        job = False

        for product_counter, channel_product in enumerate(channel_products, 1):
            if not channel_product.channel_product_tmpl_id.exported_in_channel:
                continue
            merchant_prod_no = channel_product.merchant_product_no or channel_product.product_id.default_code
            product_price = instance.pricelist_id.with_context(uom=channel_product.product_id.uom_id.id).price_get(
                channel_product.product_id.id, 1.0, partner=False)[instance.pricelist_id.id] or 0.0
            product_data = [{
                "MerchantProductNo": str(merchant_prod_no),
                "Price": product_price
            }]
            try:
                results = channel_engine_obj.get_channel_offer_api_object(instance, data=product_data) or {}
            except Exception as e:
                if not job:
                    value = {
                        'instance_id': instance.id,
                        'message': 'Update Product Price In Channel Engine.',
                        'application': 'update_product_price',
                        'operation_type': 'export',
                        'skip_process': True
                    }
                    job = channel_log_book_obj.create(value)
                job_line_val = {
                    'record_id': int(product_counter),
                    'job_id': job.id,
                    'log_type': 'error',
                    'action_type': 'skip_line',
                    'operation_type': 'export',
                    'message': 'Exception when calling OfferApi->offer_stock_price_update: %s\n' % (e),
                }
                channel_log_book_line_obj.create(job_line_val)

            if results:
                resp_success = results.get('Success', False)
                resp_content = results.get('Content', {})
                resp_content_product = resp_content.get(str(channel_product.name), '')

                if not resp_success or resp_content_product:
                    if not job:
                        value = {
                            'instance_id': instance.id,
                            'message': '%s' % (str(results.get('Message'))),
                            'application': 'update_product_price',
                            'operation_type': 'export',
                            'skip_process': True
                        }
                        job = channel_log_book_obj.create(value)
                    job_line_val = {
                        'record_id': int(product_counter),
                        'channel_order_ref': channel_product.name,
                        'job_id': job.id,
                        'log_type': 'error',
                        'action_type': 'skip_line',
                        'operation_type': 'export',
                        'message': '%s' % (str(resp_content)),
                    }
                    channel_log_book_line_obj.create(job_line_val)
        return True
