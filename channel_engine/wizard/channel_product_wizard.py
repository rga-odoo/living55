# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ChannelProductWizard(models.TransientModel):
    _name = 'channel.product.wizard'
    _description = "Channel Product Wizard"
    
    is_publish_in_channel = fields.Boolean('Start Listing Immediately',help="Will Active Product Immediately on Channel Engine")
    is_export_or_update_price = fields.Boolean(string='Export/Update Price',default=False,help="If you want to export/update product with price so Checked True other wise False.")
    is_export_or_update_stock = fields.Boolean(string='Export/Update Stock',default=False,help="If you want to export/update product with stock so Checked True other wise False.")

    

    def export_product_in_channel(self):
        self.ensure_one()
        channel_instance_obj = self.env['ce.instance']
        channel_product_tmpl_obj = self.env['channel.product.template']
        active_ids = self._context.get('active_ids',[])
        channel_instance_ids = channel_instance_obj.search([('state','=','confirmed')])
        for instance in channel_instance_ids:
            channel_product_template_ids = channel_product_tmpl_obj.search([('id','in',active_ids),('instance_id','=',instance.id),('exported_in_channel','=',False)])            
            for channel_product_template in channel_product_template_ids:
                for variant in channel_product_template.channel_variant_ids:
                    variant.map_translations()
                if channel_product_template.product_type == 'individual' :
                    channel_product_tmpl_obj.create_individual_item(channel_product_template,instance,self.is_publish_in_channel,self.is_export_or_update_price,self.is_export_or_update_stock)
                else:
                    channel_product_tmpl_obj.create_variation_item(channel_product_template,instance,self.is_publish_in_channel,self.is_export_or_update_price,self.is_export_or_update_stock)
        return True


    def update_products_in_channel(self):
        self.ensure_one()
        channel_instance_obj = self.env['ce.instance']
        channel_product_tmpl_obj = self.env['channel.product.template']
        active_ids = self._context.get('active_ids',[])
        channel_instance_ids = channel_instance_obj.search([('state','=','confirmed')])
        for instance in channel_instance_ids:
            channel_product_template_ids = channel_product_tmpl_obj.search([('id','in',active_ids),('instance_id','=',instance.id),('exported_in_channel','=',True)])            
            for channel_product_template in channel_product_template_ids:
                if channel_product_template.product_type == 'individual':
                    channel_product_tmpl_obj.update_individual_item(instance, channel_product_template)
                else:
                    channel_product_tmpl_obj.update_variation_item(instance, channel_product_template)
        return True

    

    def update_stock_in_channel(self):
        active_ids = self._context.get('active_ids',[])
        if active_ids:
            channel_instance_obj = self.env['ce.instance']
            channel_product_product_obj = self.env['channel.product.product']
            channel_instance_ids = channel_instance_obj.search([('state','=','confirmed')])
            for instance in channel_instance_ids:
                channel_products = channel_product_product_obj.search([('id','in',active_ids),('instance_id','=',instance.id),('exported_in_channel','=',True)])
                if channel_products:                               
                    channel_product_product_obj.update_product_stock_in_channel(instance, channel_products)
    

    def update_price_in_channel(self):
        active_ids = self._context.get('active_ids',[])
        if active_ids:
            channel_instance_obj = self.env['ce.instance']
            channel_product_product_obj = self.env['channel.product.product']
            channel_instance_ids = channel_instance_obj.search([('state','=','confirmed')])
            for instance in channel_instance_ids:
                channel_products = channel_product_product_obj.search([('id','in',active_ids),('instance_id','=',instance.id),('exported_in_channel','=',True)])
                if channel_products:                               
                    channel_product_product_obj.update_product_price_in_channel(instance,channel_products) 
                    
                    

    def send_order_acknowledge_in_channel(self): 
        active_ids = self._context.get('active_ids',[])
        if active_ids:
            channel_instance_obj = self.env['ce.instance']
            channel_instance_ids = channel_instance_obj.search([('state','=','confirmed')])
            sale_order_obj = self.env['sale.order']
            for instance in channel_instance_ids:
                sale_orders = sale_order_obj.search([('id','in',active_ids),('instance_id','=',instance.id),('is_send_acknowledge_order','=',False)])
                if sale_orders:                               
                    sale_order_obj.send_order_acknowledge_in_channel(instance, sale_orders)
        return True
    

    def action_download_attachment(self, attachment_ids):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/ce_download_document?attachment_ids=%s'%(attachment_ids),
            'target': 'new',
            'nodestroy': False,
         }
    

    def download_ce_dos_packing_slip(self):
        active_ids = self._context.get('active_ids',[])
        if active_ids:
            _domain = [
                ('id','in',active_ids),('ce_instance_id','!=',False),('state','not in',['cancel']),
                ('picking_type_code','=','outgoing'),('sale_id','!=',False),
                ('sale_id.state','=','sale'),('sale_id.is_send_acknowledge_order','=',True),
                ('ce_instance_id.state','=','confirmed'),('is_channel_delivery_order','=',True)
            ]
            ce_picking_ids = self.env['stock.picking'].search(_domain)
            attachment_ids = ce_picking_ids and self.env['stock.picking'].download_ce_dos_packing_slip(ce_picking_ids)
            if attachment_ids:
                return self.action_download_attachment(attachment_ids)
        return True