#!/usr/bin/python3
# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import Warning
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

_intervalTypes = {
    'days': lambda interval: relativedelta(days=interval),
    'hours': lambda interval: relativedelta(hours=interval),
    'weeks': lambda interval: relativedelta(days=7 * interval),
    'months': lambda interval: relativedelta(months=interval),
    'minutes': lambda interval: relativedelta(minutes=interval),
}


class ce_instance_config(models.TransientModel):
    _name = 'res.config.ce.instance'
    _description = "Channel Engine Res Setting"
    
    ce_name = fields.Char("Instance Name")
    ce_warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    ce_company_id = fields.Many2one('res.company', string='Company')
    ce_api_key = fields.Char('Api Key', size=256, required=True, help="Api Key")
    ce_shop_url = fields.Char('Channel Shop Url', size=256, required=True, help="Channel Shop Url")

    def create_ce_instance(self):
        ce_instance_obj = self.env['ce.instance']
        exist_instance = ce_instance_obj.search(['|', ('name', '=', self.ce_name), ('api_key', '=', self.ce_api_key)])
        if exist_instance:
            raise UserError("Instance is already exist")
        else:         
            ce_instance_obj.create({  
                'name':self.ce_name,
                'api_key':self.ce_api_key,
                'channel_shop_url':self.ce_shop_url,
                'company_id':self.ce_company_id.id,
                'warehouse_id':self.ce_warehouse_id.id,
            })        
        return True

    
class ce_config_settings(models.TransientModel):
    _inherit = 'res.config.settings'

    ce_instance_id = fields.Many2one('ce.instance', 'Instance', help="Select CE instance.")
    ce_warehouse_id = fields.Many2one('stock.warehouse', string="Channel Warehouse")
    ce_company_id = fields.Many2one('res.company', string="Channel Company")
    ce_lang_id = fields.Many2one('res.lang', string='Language')
    ce_shipment_charge_product_id = fields.Many2one("product.product", "Shipment Fee", domain=[('type', '=', 'service')])
    ce_pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')   
    ce_order_prefix = fields.Char(size=10, string='Channel Order Prefix')    

    is_auto_update_products_stock = fields.Boolean(string="Auto Update Products Stock?", default=False, help="If you want to auto update product stock so check mark True other wise False. By default it's False.")
    update_ce_stock_interval_number = fields.Integer(string='Channel Update Stock Interval Number', help="Repeat every x.")
    update_ce_stock_interval_type = fields.Selection([('minutes', 'Minutes'),
            ('hours', 'Hours'), ('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months')], string='Channel Update Stock Interval Unit')
    update_ce_stock_next_execution = fields.Datetime(string='Channel Update Stock Next Execution', help='Next execution time')
    update_ce_stock_user_id = fields.Many2one('res.users', string="CE Update Stock", help='User')

    is_auto_update_products_price = fields.Boolean(string="Auto Update Products Price?", default=False, help="If you want to auto update product price so check mark True other wise False. By default it's False.")
    update_ce_price_interval_number = fields.Integer(string='Channel Update Price Interval Number', help="Repeat every x.")
    update_ce_price_interval_type = fields.Selection([('minutes', 'Minutes'),
            ('hours', 'Hours'), ('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months')], string='Channel Update Price Interval Unit')
    update_ce_price_next_execution = fields.Datetime(string='Channel Update Price Next Execution', help='Next execution time')
    update_ce_price_user_id = fields.Many2one('res.users', string="CE Update Price", help='User')

    is_auto_import_sales_orders = fields.Boolean(string="Auto Import Orders?", default=False, help="If you want to auto import orders so check mark True other wise False. By default it's False.")
    import_ce_orders_interval_number = fields.Integer(string='Channel Import Orders Interval Number', help="Repeat every x.")
    import_ce_orders_interval_type = fields.Selection([('minutes', 'Minutes'),
            ('hours', 'Hours'), ('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months')], string='Channel Import Orders Interval Unit')
    import_ce_orders_next_execution = fields.Datetime(string='Channel Import Orders Next Execution', help='Next execution time')
    import_ce_orders_user_id = fields.Many2one('res.users', string="Channel Import Orders", help='User')

    is_auto_create_shipments = fields.Boolean(string="Auto Update Shipment?", default=False, help="If you want to auto update shipment so check mark True other wise False. By default it's False.")
    create_ce_shipment_interval_number = fields.Integer(string='Channel Update Shipment Interval Number', help="Repeat every x.")
    create_ce_shipment_interval_type = fields.Selection([('minutes', 'Minutes'),
            ('hours', 'Hours'), ('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months')], string='Channel Update Shipment Interval Unit')
    create_ce_shipment_next_execution = fields.Datetime(string='Channel Update Shipment Next Execution', help='Next execution time')
    create_ce_shipment_user_id = fields.Many2one('res.users', string="CE Update Shipment", help='User')
    
    is_auto_import_ce_products = fields.Boolean(string="Auto Import Products?", default=False, help="If you want to auto import products so check mark True other wise False. By default it's False.")
    import_ce_products_interval_number = fields.Integer(string='Auto Import Products Interval Number', help="Repeat every x.")
    import_ce_products_interval_type = fields.Selection([('minutes', 'Minutes'),
            ('hours', 'Hours'), ('days', 'Days'), ('weeks', 'Weeks'), ('months', 'Months')], string='Import product interval unit.')
    import_ce_products_next_execution = fields.Datetime(string='Auto Import Products Next Execution', help='Next execution time')
    import_ce_products_user_id = fields.Many2one('res.users', string="Auto Import Products User", help='Import product user.')
    
    is_order_confirm_to_auto_send_ack = fields.Boolean(string="Do you want to confirm sale to send ack.?", default=False, help="Checked True to auto send order acknowledgement in channel engine when channel sale order confirm.")
        
    @api.onchange('ce_instance_id')
    def onchange_ce_instance_id(self):
        instance = self.ce_instance_id
        if instance:
            self.ce_warehouse_id = instance.warehouse_id and instance.warehouse_id.id or False
            self.ce_company_id = instance.company_id and instance.company_id.id or False
            self.ce_lang_id = instance.lang_id or False
            self.ce_shipment_charge_product_id = instance.shipment_charge_product_id and instance.shipment_charge_product_id.id or False
            self.ce_order_prefix = instance and instance.order_prefix or False
            self.ce_pricelist_id = instance.pricelist_id and instance.pricelist_id.id or False         
            
            # Import Order
            self.is_auto_update_products_stock = instance.is_auto_update_products_stock or False
            self.update_ce_stock_interval_number = instance.update_ce_stock_interval_number or False
            self.update_ce_stock_next_execution = instance.update_ce_stock_next_execution or False
            self.update_ce_stock_user_id = instance.update_ce_stock_user_id.id or False
                        
            self.is_auto_update_products_price = instance.is_auto_update_products_price or False
            self.update_ce_price_interval_number = instance.update_ce_price_interval_number or False
            self.update_ce_price_interval_type = instance.update_ce_price_interval_type or False
            self.update_ce_price_next_execution = instance.update_ce_price_next_execution or False
            self.update_ce_price_user_id = instance.update_ce_price_user_id.id or False
            
            self.is_auto_import_sales_orders = instance.is_auto_import_sales_orders or False
            self.import_ce_orders_interval_number = instance.import_ce_orders_interval_number or False
            self.import_ce_orders_interval_type = instance.import_ce_orders_interval_type or False
            self.import_ce_orders_next_execution = instance.import_ce_orders_next_execution or False
            self.import_ce_orders_user_id = instance.import_ce_orders_user_id.id or False
            
            self.is_auto_create_shipments = instance.is_auto_create_shipments or False
            self.create_ce_shipment_interval_number = instance.create_ce_shipment_interval_number or False
            self.create_ce_shipment_interval_type = instance.create_ce_shipment_interval_type or False
            self.create_ce_shipment_next_execution = instance.create_ce_shipment_next_execution or False
            self.create_ce_shipment_user_id = instance.create_ce_shipment_user_id.id or False
            
            self.is_auto_import_ce_products = instance.is_auto_import_ce_products or False
            self.import_ce_products_interval_number = instance.import_ce_products_interval_number or False
            self.import_ce_products_interval_type = instance.import_ce_products_interval_type or False
            self.import_ce_products_next_execution = instance.import_ce_products_next_execution or False
            self.import_ce_products_user_id = instance.import_ce_products_user_id or False
            self.is_order_confirm_to_auto_send_ack = instance.is_order_confirm_to_auto_send_ack or False

            # Auto Update Products
            try:
                ce_update_stock_cron_exist = self.env.ref('channel_engine.ir_cron_auto_update_products_stock_%d' % (instance.id), raise_if_not_found=False)
            except:
                ce_update_stock_cron_exist = False
            if ce_update_stock_cron_exist:
                self.update_ce_stock_interval_number = ce_update_stock_cron_exist.interval_number or False
                self.update_ce_stock_interval_type = ce_update_stock_cron_exist.interval_type or False
                self.update_ce_stock_next_execution = ce_update_stock_cron_exist.nextcall or False
                self.update_ce_stock_user_id = ce_update_stock_cron_exist.user_id.id or False
            
            # Auto Update Price
            try:
                ce_update_price_cron_exist = self.env.ref('channel_engine.ir_cron_auto_update_products_price_%d' % (instance.id), raise_if_not_found=False)
                            
            except:
                ce_update_price_cron_exist = False
            if ce_update_price_cron_exist:
                self.update_ce_price_interval_number = ce_update_price_cron_exist.interval_number or False
                self.update_ce_price_interval_type = ce_update_price_cron_exist.interval_type or False
                self.update_ce_price_next_execution = ce_update_price_cron_exist.nextcall or False
                self.update_ce_price_user_id = ce_update_price_cron_exist.user_id.id or False
            
            # Auto Import Order
            try:
                ce_order_import_cron_exist = self.env.ref('channel_engine.ir_cron_auto_import_sales_orders_%d' % (instance.id), raise_if_not_found=False)
            except:
                ce_order_import_cron_exist = False
            if ce_order_import_cron_exist:
                self.import_ce_orders_interval_number = ce_order_import_cron_exist.interval_number or False
                self.import_ce_orders_interval_type = ce_order_import_cron_exist.interval_type or False
                self.import_ce_orders_next_execution = ce_order_import_cron_exist.nextcall or False
                self.import_ce_orders_user_id = ce_order_import_cron_exist.user_id.id or False
            
            # Auto Send Shipment
            try:
                ce_shipment_cron_exist = self.env.ref('channel_engine.ir_cron_auto_create_shipment_%d' % (instance.id), raise_if_not_found=False)
            except:
                ce_shipment_cron_exist = False
            if ce_shipment_cron_exist:
                self.create_ce_shipment_interval_number = ce_shipment_cron_exist.interval_number or False
                self.create_ce_shipment_interval_type = ce_shipment_cron_exist.interval_type or False
                self.create_ce_shipment_next_execution = ce_shipment_cron_exist.nextcall or False
                self.create_ce_shipment_user_id = ce_shipment_cron_exist.user_id.id or False
                
            # Auto Import Product
            try:
                auto_import_products_cron_exist = self.env.ref('channel_engine.import_ce_products_user_id_%d' % (instance.id), raise_if_not_found=False)
            except:
                auto_import_products_cron_exist = False
            if auto_import_products_cron_exist:
                self.import_ce_products_interval_number = auto_import_products_cron_exist.interval_number or False
                self.import_ce_products_interval_type = auto_import_products_cron_exist.interval_type or False
                self.import_ce_products_next_execution = auto_import_products_cron_exist.nextcall or False
                self.import_ce_products_user_id = auto_import_products_cron_exist.user_id.id or False

    def execute(self):
        values = {}
        instance = self.ce_instance_id or False
        res = super(ce_config_settings, self).execute()
        if instance:
            values['warehouse_id'] = self.ce_warehouse_id and self.ce_warehouse_id.id or False
            values['lang_id'] = self.ce_lang_id and self.ce_lang_id.id or False
            values['company_id'] = self.ce_company_id and self.ce_company_id.id or False
            values['order_prefix'] = self.ce_order_prefix and self.ce_order_prefix
            values['pricelist_id'] = self.ce_pricelist_id and self.ce_pricelist_id.id or False 
            values['shipment_charge_product_id'] = self.ce_shipment_charge_product_id and self.ce_shipment_charge_product_id.id or False
                        
            values['is_auto_update_products_stock'] = self.is_auto_update_products_stock or False
            values['update_ce_stock_interval_number'] = self.update_ce_stock_interval_number or False
            values['update_ce_stock_interval_type'] = self.update_ce_stock_interval_type or False
            values['update_ce_stock_next_execution'] = self.update_ce_stock_next_execution or False
            values['update_ce_stock_user_id'] = self.update_ce_stock_user_id.id or False
              
            values['is_auto_update_products_price'] = self.is_auto_update_products_price or False
            values['update_ce_price_interval_number'] = self.update_ce_price_interval_number or False
            values['update_ce_price_interval_type'] = self.update_ce_price_interval_type or False
            values['update_ce_price_next_execution'] = self.update_ce_price_next_execution or False
            values['update_ce_price_user_id'] = self.update_ce_price_user_id.id or False
            
            values['is_auto_import_sales_orders'] = self.is_auto_import_sales_orders or False
            values['import_ce_orders_interval_number'] = self.import_ce_orders_interval_number or False
            values['import_ce_orders_interval_type'] = self.import_ce_orders_interval_type or False
            values['import_ce_orders_next_execution'] = self.import_ce_orders_next_execution or False
            values['import_ce_orders_user_id'] = self.import_ce_orders_user_id.id or False
            
            values['is_auto_create_shipments'] = self.is_auto_create_shipments or False
            values['create_ce_shipment_interval_number'] = self.create_ce_shipment_interval_number or False
            values['create_ce_shipment_interval_type'] = self.create_ce_shipment_interval_type or False
            values['create_ce_shipment_next_execution'] = self.create_ce_shipment_next_execution or False
            values['create_ce_shipment_user_id'] = self.create_ce_shipment_user_id.id or False
            
            values['is_auto_import_ce_products'] = self.is_auto_import_ce_products or False
            values['import_ce_products_interval_number'] = self.import_ce_products_interval_number or False
            values['import_ce_products_interval_type'] = self.import_ce_products_interval_type or False
            values['import_ce_products_next_execution'] = self.import_ce_products_next_execution or False
            values['import_ce_products_user_id'] = self.import_ce_products_user_id.id or False
            
            values['is_order_confirm_to_auto_send_ack'] = self.is_order_confirm_to_auto_send_ack or False
            
            instance.write(values)
            self.ce_setup_update_stock_cron(instance)
            self.ce_setup_update_price_cron(instance)
            self.ce_setup_import_orders_cron(instance)
            self.ce_setup_create_shipment_cron(instance)
            self.ce_setup_auto_import_cron(instance)
        return res

    def ce_setup_update_stock_cron(self, instance):
        if self.is_auto_update_products_stock:
            try:
                cron_exist = self.env.ref('channel_engine.ir_cron_auto_update_products_stock_%d' % (instance.id), raise_if_not_found=False)
            except:
                cron_exist = False
            nextcall = datetime.now()
            nextcall += _intervalTypes[self.update_ce_stock_interval_type](self.update_ce_stock_interval_number)
            
            vals = {
                    'active' : True,
                    'interval_number':self.update_ce_stock_interval_number,
                    'interval_type':self.update_ce_stock_interval_type,
                    'nextcall':nextcall.strftime('%Y-%m-%d %H:%M:%S'),
                    'user_id': self.update_ce_stock_user_id and self.update_ce_stock_user_id.id,
                    'code': "model.auto_update_products_stock_in_channel({'instance_id':%d})" % (instance.id)
                    }
                    
            if cron_exist:
                vals.update({'name' : cron_exist.name})
                cron_exist.write(vals)
            else:
                try:
                    ce_update_stock_cron_exist = self.env.ref('channel_engine.ir_cron_auto_update_products_stock')
                except:
                    ce_update_stock_cron_exist = False
                if not ce_update_stock_cron_exist:
                    raise UserError('Core settings of Channel are deleted, please upgrade channel engine Connector module to back this settings.')
                
                name = instance.name + ' : ' + ce_update_stock_cron_exist.name
                vals.update({'name' : name})
                new_cron = ce_update_stock_cron_exist.copy(default=vals)
                self.env['ir.model.data'].create({'module':'channel_engine',
                                                  'name':'ir_cron_auto_update_products_stock_%d' % (instance.id),
                                                  'model': 'ir.cron',
                                                  'res_id' : new_cron.id,
                                                  'noupdate' : True
                                                  })
        else:
            try:
                cron_exist = self.env.ref('channel_engine.ir_cron_auto_update_products_stock_%d' % (instance.id))
            except:
                cron_exist = False
            
            if cron_exist:
                cron_exist.write({'active':False})
        return True

    def ce_setup_update_price_cron(self, instance):
        if self.is_auto_update_products_price:
            try:
                cron_exist = self.env.ref('channel_engine.ir_cron_auto_update_products_price_%d' % (instance.id), raise_if_not_found=False)
            except:
                cron_exist = False
            nextcall = datetime.now()
            nextcall += _intervalTypes[self.update_ce_price_interval_type](self.update_ce_price_interval_number)
            
            vals = {
                    'active' : True,
                    'interval_number':self.update_ce_price_interval_number,
                    'interval_type':self.update_ce_price_interval_type,
                    'nextcall':nextcall.strftime('%Y-%m-%d %H:%M:%S'),
                    'user_id': self.update_ce_price_user_id and self.update_ce_price_user_id.id,
                    'code': "model.auto_update_products_price_in_channel({'instance_id':%d})" % (instance.id)
                    }
                    
            if cron_exist:
                vals.update({'name' : cron_exist.name})
                cron_exist.write(vals)
            else:
                try:
                    ce_update_price_cron_exist = self.env.ref('channel_engine.ir_cron_auto_update_products_price')
                except:
                    ce_update_price_cron_exist = False
                if not ce_update_price_cron_exist:
                    raise UserError('Core settings of Channel are deleted, please upgrade channel engine Connector module to back this settings.')
                
                name = instance.name + ' : ' + ce_update_price_cron_exist.name
                vals.update({'name' : name})
                new_cron = ce_update_price_cron_exist.copy(default=vals)
                self.env['ir.model.data'].create({'module':'channel_engine',
                                                  'name':'ir_cron_auto_update_products_price_%d' % (instance.id),
                                                  'model': 'ir.cron',
                                                  'res_id' : new_cron.id,
                                                  'noupdate' : True
                                                  })
        else:
            try:
                cron_exist = self.env.ref('channel_engine.ir_cron_auto_update_products_price_%d' % (instance.id))
            except:
                cron_exist = False
            
            if cron_exist:
                cron_exist.write({'active':False})
        return True

    def ce_setup_import_orders_cron(self, instance):
        if self.is_auto_import_sales_orders:
            try:
                cron_exist = self.env.ref('channel_engine.ir_cron_auto_import_sales_orders_%d' % (instance.id), raise_if_not_found=False)
            except:
                cron_exist = False
            nextcall = datetime.now()
            nextcall += _intervalTypes[self.import_ce_orders_interval_type](self.import_ce_orders_interval_number)
            
            vals = {
                'active' : True,
                'interval_number':self.import_ce_orders_interval_number,
                'interval_type':self.import_ce_orders_interval_type,
                'nextcall':nextcall.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': self.import_ce_orders_user_id and self.import_ce_orders_user_id.id,
                'code': "model.auto_import_sales_orders_in_channel({'instance_id':%d})" % (instance.id)
            }
                    
            if cron_exist:
                vals.update({'name' : cron_exist.name})
                cron_exist.write(vals)
            else:
                try:
                    ce_order_import_cron_exist = self.env.ref('channel_engine.ir_cron_auto_import_sales_orders')
                except:
                    ce_order_import_cron_exist = False
                if not ce_order_import_cron_exist:
                    raise UserError('Core settings of Channel are deleted, please upgrade channel engine Connector module to back this settings.')
                
                name = instance.name + ' : ' + ce_order_import_cron_exist.name
                vals.update({'name' : name})
                new_cron = ce_order_import_cron_exist.copy(default=vals)
                self.env['ir.model.data'].create({'module':'channel_engine',
                                                  'name':'ir_cron_auto_import_sales_orders_%d' % (instance.id),
                                                  'model': 'ir.cron',
                                                  'res_id' : new_cron.id,
                                                  'noupdate' : True
                                                  })
        else:
            try:
                cron_exist = self.env.ref('channel_engine.ir_cron_auto_import_sales_orders_%d' % (instance.id))
            except:
                cron_exist = False
            
            if cron_exist:
                cron_exist.write({'active':False})
        return True

    def ce_setup_create_shipment_cron(self, instance):
        if self.is_auto_create_shipments:
            try:
                cron_exist = self.env.ref('channel_engine.ir_cron_auto_create_shipment_%d' % (instance.id), raise_if_not_found=False)
            except:
                cron_exist = False
            nextcall = datetime.now()
            nextcall += _intervalTypes[self.create_ce_shipment_interval_type](self.create_ce_shipment_interval_number)
            
            vals = {
                'active' : True,
                'interval_number':self.create_ce_shipment_interval_number,
                'interval_type':self.create_ce_shipment_interval_type,
                'nextcall':nextcall.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': self.create_ce_shipment_user_id and self.create_ce_shipment_user_id.id,
                'code': "model.auto_create_shipment_in_channel({'instance_id':%d})" % (instance.id)
            }
                    
            if cron_exist:
                vals.update({'name' : cron_exist.name})
                cron_exist.write(vals)
            else:
                try:
                    ce_shipment_cron_exist = self.env.ref('channel_engine.ir_cron_auto_create_shipment')
                except:
                    ce_shipment_cron_exist = False
                if not ce_shipment_cron_exist:
                    raise UserError('Core settings of Channel are deleted, please upgrade channel engine Connector module to back this settings.')
                
                name = instance.name + ' : ' + ce_shipment_cron_exist.name
                vals.update({'name' : name})
                new_cron = ce_shipment_cron_exist.copy(default=vals)
                self.env['ir.model.data'].create({'module':'channel_engine',
                                                  'name':'ir_cron_auto_create_shipment_%d' % (instance.id),
                                                  'model': 'ir.cron',
                                                  'res_id' : new_cron.id,
                                                  'noupdate' : True
                                                  })
        else:
            try:
                cron_exist = self.env.ref('channel_engine.ir_cron_auto_create_shipment_%d' % (instance.id))
            except:
                cron_exist = False
            
            if cron_exist:
                cron_exist.write({'active':False})
        return True

    def ce_setup_auto_import_cron(self, instance):
        if self.is_auto_import_ce_products:
            try:
                cron_exist = self.env.ref('channel_engine.ir_cron_auto_import_products_%d' % (instance.id), raise_if_not_found=False)
            except:
                cron_exist = False
            nextcall = datetime.now()
            nextcall += _intervalTypes[self.import_ce_products_interval_type](self.import_ce_products_interval_number)
            
            vals = {
                'active' : True,
                'interval_number': self.import_ce_products_interval_number,
                'interval_type': self.import_ce_products_interval_type,
                'nextcall': nextcall.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': self.import_ce_products_user_id and self.import_ce_products_user_id.id,
                'code': "model.auto_imoprt_products_from_ce({'instance_id':%d})" % (instance.id)
            }

            if cron_exist:
                vals.update({'name' : cron_exist.name})
                cron_exist.write(vals)
            else:
                try:
                    auto_import_products_cron_exist = self.env.ref('channel_engine.ir_cron_auto_import_products')
                except:
                    auto_import_products_cron_exist = False
                if not auto_import_products_cron_exist:
                    raise UserError('Core settings of Channel are deleted, please upgrade channel engine Connector module to back this settings.')
                
                name = instance.name + ' : ' + auto_import_products_cron_exist.name
                vals.update({'name' : name})
                new_cron = auto_import_products_cron_exist.copy(default=vals)
                self.env['ir.model.data'].create({
                    'module':'channel_engine',
                    'name':'ir_cron_auto_import_products_%d' % (instance.id),
                    'model': 'ir.cron',
                    'res_id' : new_cron.id,
                    'noupdate' : True
                })
        else:
            try:
                cron_exist = self.env.ref('channel_engine.ir_cron_auto_import_products_%d' % (instance.id))
            except:
                cron_exist = False
            
            if cron_exist:
                cron_exist.write({'active':False})
        return True
