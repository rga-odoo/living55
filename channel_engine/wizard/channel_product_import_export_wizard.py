# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ChannelProcessImportExport(models.TransientModel):
    _name = 'channel.process.import.export'
    _description = "Channel Engine Import Export Process"

    instance_ids = fields.Many2many("ce.instance", 'channel_import_export_rel', 'process_id', 'instance_id',
                                    "Instances", required=True)
    is_import_product = fields.Boolean("Import Products", default=False,
                                       help="Import product from Channel Engine to ERP.")
    is_export_product = fields.Boolean("Export Products", default=False,
                                       help="Export product from ERP to Channel Engine.")
    is_publish_in_channel = fields.Boolean('Start Listing Immediately',
                                           help="Will Active Product Immediately on Channel Engine")
    is_update_stock = fields.Boolean("Update Stock", default=False, help="Update Product Stock ERP to Channel Engine.")
    is_update_price = fields.Boolean("Update Price", default=False, help="Update Product Pice ERP to channel Engine.")
    is_import_sales_orders = fields.Boolean("Import Sales Order", default=False,
                                            help="Sales Order import from channel engine.")
    is_send_acknowledge_order = fields.Boolean(string='Send Order Acknowledge', default=False,
                                               help="True if already send Order Acknowledge other wise False. By default set False.")
    is_create_shipment = fields.Boolean(string='Create Shipment', default=False,
                                        help="Update order(Mark (part of) an order as shipped.) Status, Merchant Shipment No ,Tracking Number, Track Trace URL in channel engine.")
    is_download_order_packing_slip = fields.Boolean(string="Download Order Packing Slip", default=False,
                                                    help="This option True to download packing slip for channel order from channel engine.")

    def execute(self):
        channel_product_product_obj = self.env['channel.product.product']
        channel_product_template_obj = self.env['channel.product.template']
        sale_order_obj = self.env['sale.order']

        instances = []
        if self.instance_ids:
            instances = self.instance_ids
        else:
            return True

        if self.is_export_product:
            self.export_product_in_channel()
        if self.is_update_stock:
            for instance in instances:
                channel_product_product_obj.update_product_stock_in_channel(instance)
        if self.is_update_price:
            for instance in instances:
                channel_product_product_obj.update_product_price_in_channel(instance)
        if self.is_import_sales_orders:
            for instance in instances:
                sale_order_obj.import_sales_order_from_channel(instance)
        if self.is_send_acknowledge_order:
            for instance in instances:
                sale_orders = sale_order_obj.search(
                    [('instance_id', '=', instance.id), ('is_send_acknowledge_order', '=', False)])
                sale_order_obj.send_order_acknowledge_in_channel(instance, sale_orders)
        if self.is_create_shipment:
            for instance in instances:
                sale_order_obj.create_shipment_in_channel(instance)
        if self.is_import_product:
            channel_product_template_obj.import_products_from_channel_engine(instances)
        if self.is_download_order_packing_slip:
            sale_order_obj.download_ce_order_packing_slip(instances)
        return True

    def export_product_in_channel(self):
        channel_product_template_obj = self.env['channel.product.template']
        instances = self.instance_ids if self.instance_ids else ''
        for instance in instances:
            channel_product_template_ids = channel_product_template_obj.search(
                [('instance_id', '=', instance.id), ('exported_in_channel', '=', False)])
            for channel_product_template in channel_product_template_ids:
                if (channel_product_template.product_type == 'individual') or (
                        len(channel_product_template.channel_variant_ids.ids) == 1):
                    channel_product_template_obj.create_individual_item(channel_product_template, instance,
                                                                        self.is_publish_in_channel,
                                                                        is_export_or_update_price=False,
                                                                        is_export_or_update_stock=False)
                else:
                    channel_product_template_obj.create_variation_item(channel_product_template, instance,
                                                                       self.is_publish_in_channel,
                                                                       is_export_or_update_price=False,
                                                                       is_export_or_update_stock=False)
        return True

    def get_description(self, instance_id, product_id):
        if instance_id.prod_description_erpify:
            return product_id[instance_id.prod_description_erpify.name]
        else:
            return product_id.description_sale

    def get_title(self, instance_id, product_id):
        if instance_id.prod_title_erpify:
            return product_id[instance_id.prod_title_erpify.name]
        else:
            return product_id.name

    def prepare_product_for_export(self):
        channel_product_template_obj = self.env['channel.product.template']
        channel_product_product_obj = self.env['channel.product.product']
        template_active_ids = self._context.get('active_ids', [])
        product_template_ids = self.env['product.template'].search(
            [('id', 'in', template_active_ids), ('type', '!=', 'service')])
        for instance in self.instance_ids:
            for product_template in product_template_ids:
                channel_product_tmpl = channel_product_template_obj.search(
                    [('instance_id', '=', instance.id), ('product_tmpl_id', '=', product_template.id)])
                if not channel_product_tmpl:
                    vals = {'instance_id': instance.id, 'product_tmpl_id': product_template.id,
                            'name': self.get_title(instance, product_template)}
                    if len(product_template.product_variant_ids.ids) == 1:
                        vals.update({'product_type': 'individual'})
                        channel_product_tmpl = channel_product_template_obj.create(vals)
                    else:
                        vals.update({'product_type': 'variation'})
                        channel_product_tmpl = channel_product_template_obj.create(vals)
                for product_variant in product_template.product_variant_ids:
                    channel_product_variant = channel_product_product_obj.search(
                        [('instance_id', '=', instance.id), ('product_id', '=', product_variant.id)])
                    if not channel_product_variant:
                        vals = {'instance_id': instance.id, 'product_id': product_variant.id,
                                'channel_product_tmpl_id': channel_product_tmpl.id,
                                'merchant_product_no': product_variant.default_code,
                                'name': self.get_title(instance, product_variant) or self.get_title(instance, product_template),
                                'description': self.get_description(instance, product_variant) or self.get_description(instance, product_template)}
                        channel_product_product_obj.create(vals)
                    else:
                        vals = {'name': self.get_title(instance, product_variant) or self.get_title(instance, product_template),
                                'description': self.get_description(instance, product_variant) or self.get_description(instance, product_template)}
                        channel_product_variant.write(vals)
        return True
