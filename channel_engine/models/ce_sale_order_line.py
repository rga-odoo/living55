# -*- coding: utf-8 -*-
import time
from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    channel_product_qty = fields.Float("Channel Product Qty",help="Channel product qty.")
    channel_product_no = fields.Char("Channel Product No",size=50,help="Channel product number.")
    instance_id = fields.Many2one('ce.instance',related="order_id.instance_id",string='Instance',help="Channel Instance",readonly=True)
    
    @api.model
    def create_channel_account_tax(self,value,price_included,company):
        account_tax_obj = self.env['account.tax']
        if price_included:
            name = '%s_(%s %s included %s)_%s'%('Sales Tax Price Included',str(value),'%',price_included and 'T' or 'F',company.name)
        else:
            name='%s_(%s %s excluded %s)_%s'%('Sales Tax Price Excluded',str(value),'%',price_included and 'F' or 'T',company.name)
        account_tax_id = account_tax_obj.create({'name':name,'amount':float(value),'type_tax_use':'sale','price_include':price_included,'company_id':company.id})
        
        return account_tax_id
    
    @api.model
    def get_channel_tax_id(self, instance, amount):
        account_tax_obj = self.env['account.tax']
        tax_id=[]
        if amount != 0.0:
            acc_tax_id = account_tax_obj.search([('price_include','=',True),('type_tax_use', '=', 'sale'), ('amount', '=', amount),('company_id','=',instance.warehouse_id and instance.warehouse_id.company_id.id)])
            if not acc_tax_id:
                acc_tax_id = self.create_channel_account_tax(amount,True,instance.warehouse_id and instance.warehouse_id.company_id)
            if acc_tax_id:
                tax_id = [(6, 0, acc_tax_id.ids)]
        else:
            tax_id=[]        
        return tax_id   

    def _get_map_order_line_status(self, instance, order_dict):
        channel_order_status = order_dict.get('Status','')
        if channel_order_status:
            if channel_order_status == 'NEW':
                channel_order_status = 'draft'
            elif channel_order_status == 'IN_PROGRESS':
                channel_order_status = 'draft'
            elif channel_order_status == 'SHIPPED':
                channel_order_status = 'draft'
        else:
            channel_order_status = 'draft'
        return channel_order_status

    def create_channel_sale_order_line_dict(self, instance, order_line_dict, price_unit, channel_product, odoo_product, channel_order, product_title, partner, partner_vals_dict,order_line_status):
        sale_order_line_obj = self.env['sale.order.line']
        product_name = product_title or (channel_product and channel_product.name)
        uom_id = odoo_product and odoo_product.uom_id and odoo_product.uom_id.id
        product_qty = order_line_dict.get('Quantity') if order_line_dict else 1.0
        product_id = odoo_product and odoo_product.id
        #fiscal_position = partner and partner.property_account_position
        sequence = 100
        tax_id = []
        #product_vals = sale_order_line_obj.product_id_change(partner_vals_dict.get('pricelist_id'),product_id,product_qty,uom_id,product_qty,False,product_name,partner and partner.id,False,True,time.strftime('%Y-%m-%d'),False,fiscal_position.id,False)
        new_record = sale_order_line_obj.new({'product_id': odoo_product and odoo_product.id or False,'product_uom': uom_id,'name':product_name})
        new_record.product_id_change()
        
        product_vals=self.env['sale.order.line']._convert_to_write({name: new_record[name] for name in new_record._cache})
        
        #product_vals = product_vals.get('value')

#         if product_vals.get('tax_id',[]):
#             tax_id=[(6,0,product_vals.get('tax_id',[]))]
#          elif instance.tax_id:
#              tax_id = [(6,0,[instance.tax_id.id])] 
        
        product_vals.update({
            'name': product_name,
            'product_id': product_id,
            'product_uom': uom_id,
            'product_uom_qty' : product_qty,
            'price_unit': price_unit or 0.0,
            'order_id': channel_order and channel_order.id or False,
            'instance_id': instance.id,
            'state': order_line_status if order_line_status else 'draft',
            'sequence': sequence,
            'channel_product_no': order_line_dict.get('ChannelProductNo',''),
            'channel_product_qty': product_qty,
            #'tax_id': tax_id
        })
        return product_vals

    def create_channel_sale_order_line(self, instance, channel_order, order_dict, partner, partner_vals_dict, is_already_shipment_line):
        channel_product_product_obj = self.env['channel.product.product']
        product_product_obj = self.env['product.product'] 
        order_lines = order_dict and order_dict.get('Lines',[])
        odoo_product = False
        
        for order_line_dict in order_lines:
            merchant_product_no = order_line_dict.get('MerchantProductNo','')
            order_line_status = self._get_map_order_line_status(instance,order_dict)
            channel_products = channel_product_product_obj.search([('merchant_product_no','=',merchant_product_no),('instance_id','=',instance.id)],limit=1)
            if channel_products:
                odoo_product = channel_products.product_id
            else:
                odoo_product = product_product_obj.search([('default_code','=',merchant_product_no)],limit=1)
            
            if (not channel_products and not odoo_product) or (not odoo_product):
                continue 
            
            price_unit = order_line_dict.get('UnitPriceInclVat',0.0)
            order_line_vals_dict = self.create_channel_sale_order_line_dict(instance,order_line_dict,price_unit,channel_products,odoo_product,channel_order,odoo_product and odoo_product.name,partner,partner_vals_dict,order_line_status)
            order_line_vals_dict and self.create(order_line_vals_dict)
        return True