# -*- coding: utf-8 -*-
import cgi, re
from odoo.exceptions import Warning
from odoo import models, fields, api, _
from odoo.addons.channel_engine.channel_engine_api.api import ChannelEngine


class ChannelProductTemplate(models.Model):
    _name = "channel.product.template"
    _description = "Channel Product Template"

    name = fields.Char('Product Name', size=256, required=True, translate=True, help="Insert Product Name.")
    instance_id = fields.Many2one('ce.instance', string='Instance', required=True, help="Instance Name")
    product_tmpl_id = fields.Many2one("product.template", string="ERP Product", required=True)
    product_type = fields.Selection([('variation', 'Variation'), ('individual', 'Individual')], string='Product Type', help="Product Type.")
    product_brand_id = fields.Many2one('channel.product.brand', string="Product Brand", help="Product brand name.")
    channel_variant_ids = fields.One2many("channel.product.product", "channel_product_tmpl_id", "Variants")
    exported_in_channel = fields.Boolean("Exported Product To Channel ?", help="Exported product in channel engine?")
    count_total_variants = fields.Integer("Total Variants", compute="_compute_total_variants")
    count_exported_variants = fields.Integer("Exported Variants", compute="_compute_total_variants")
    count_active_variants = fields.Integer("Active Variants", compute="_compute_total_variants")

    def _compute_total_variants(self):
        for record in self :
            record.update({
                'count_total_variants': len(record.channel_variant_ids),
                'count_exported_variants': sum(record.channel_variant_ids.mapped('exported_in_channel')),
                'count_active_variants': sum(record.channel_variant_ids.mapped('is_active_in_channel'))
            })

    def cleanhtml(self, raw_html):
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext

    def get_description(self):
        if self.instance_id.prod_description_erpify:
            return self.product_tmpl_id[self.instance_id.prod_description_erpify.name] or ''
        else:
            return self.product_tmpl_id.sale_description

    def get_title(self):
        if self.instance_id.prod_title_erpify:
            return self.product_tmpl_id[self.instance_id.prod_title_erpify.name] or ''
        else:
            return self.product_tmpl_id.name

    def prepare_individual_item_dict(self, channel_product_template, variant, instance, product_type, is_publish_in_channel, is_export_or_update_price, is_export_or_update_stock):
        product_attribute_obj = self.env['product.attribute']
        channel_product_product_obj = self.env['channel.product.product']
        
        odoo_product_id = variant and variant.product_id or False
        prod_name = self.cleanhtml(cgi.escape(variant.get_title() or channel_product_template.get_title()))
        prod_brand_name = channel_product_template.product_brand_id and channel_product_template.product_brand_id.name or '' 
        merchant_prod_no = variant.merchant_product_no or variant.product_id.default_code
        prod_description = self.cleanhtml(cgi.escape(variant.get_description() or channel_product_template.get_description()))
        ean13 = variant.ean13 or ''
        warehouse_id = instance.warehouse_id and instance.warehouse_id.id        
        stock = channel_product_product_obj.get_channel_product_stock(variant, warehouse_id, instance.stock_field.name)
        # image_url = variant.image_url or ''
        purchase_price = (variant.product_id.standard_price or 0.0) if (variant.product_id and variant.product_id.standard_price) else 0.0
        seller_ids = variant.product_id and variant.product_id.seller_ids
        manufacturer_product_number = (seller_ids[0].product_code or "") if seller_ids else ""
        category_trail = odoo_product_id.categ_id.name_get()[0][1] if (odoo_product_id and odoo_product_id.categ_id) else ""
        product_price = variant.product_id.with_context({'pricelist':instance.pricelist_id.id, 'quantity':1}).price
        catalog_price = product_price if product_price else 0.0
        product_size = ''
        product_color = ''
        
        product_dict_vals = {
            'MerchantProductNo' : str(merchant_prod_no) ,
            'Name' :prod_name ,
            'Description' : prod_description ,
            'Brand' :prod_brand_name,
            'ManufacturerProductNumber':manufacturer_product_number,
            'Stock' : int(stock) ,
            'Price' : product_price,
            'MSRP':catalog_price,
            'PurchasePrice': purchase_price,
            # 'ImageUrl' : image_url,
            'CategoryTrail':category_trail
        }
        
        ean13 and product_dict_vals.update({'Ean' : ean13})
        product_dict = [product_dict_vals]
        # Prepare Image Dictionary
        if instance.use_website_images_or_ce_images:
            image_ids = variant.product_id.product_template_image_ids
            if variant.product_id.image_1920:
                image_url_erpify = variant.product_id.main_image_url
                product_dict[0].update({'ImageUrl': image_url_erpify})
            image_url_kyes = [
                'ExtraImageUrl1', 'ExtraImageUrl2', 'ExtraImageUrl3',
                'ExtraImageUrl4', 'ExtraImageUrl5', 'ExtraImageUrl6',
                'ExtraImageUrl7', 'ExtraImageUrl8', 'ExtraImageUrl9'
            ]
            for image_counter, image_id in enumerate(image_ids, 0):
                if image_counter == len(image_url_kyes):
                    break
                if not image_id.image_url:  # image_id.ce_image_url:
                    continue
                product_dict[0].update({
                    image_url_kyes[image_counter]: image_id.image_url or ''
                })
        else:
            image_ids = variant.ce_product_image_ids
            image_url_kyes = [
                'ImageUrl', 'ExtraImageUrl1', 'ExtraImageUrl2', 'ExtraImageUrl3',
                'ExtraImageUrl4', 'ExtraImageUrl5', 'ExtraImageUrl6',
                'ExtraImageUrl7', 'ExtraImageUrl8', 'ExtraImageUrl9'
            ]
            for image_counter, image_id in enumerate(image_ids, 0):
                if image_counter == len(image_url_kyes):
                    break
                if not image_id.ce_image_url:
                    continue
                product_dict[0].update({
                    image_url_kyes[image_counter]: image_id.ce_image_url or ''
                })
        e_data = variant.get_translated_data()
        print(e_data)
        if instance.use_product_or_variants:
            for f in instance.prod_extra_fields_erpify:
                e_data.append(
                    {"key": f.field_description, "Value": variant.product_id[f.name], "Type": "TEXT", "IsPublic": True})
        else:
            for f in instance.prod_temp_extra_fields_erpify:
                e_data.append({"key": f.field_description, "Value": channel_product_template.product_tmpl_id[f.name],
                               "Type": "TEXT", "IsPublic": True})

        product_dict[0].update({"ExtraData": e_data})
        print(product_dict)
        return product_dict or {}

    def create_individual_item(self, channel_product_template, instance, is_publish_in_channel, is_export_or_update_price, is_export_or_update_stock):
        channel_log_book_obj = self.env['channel.log.book']
        channel_log_book_line_obj = self.env['channel.log.book.line']
        channel_engine_obj = ChannelEngine()
        channel_variant_ids = channel_product_template.channel_variant_ids
        results = False
        job = False
        
        for product_counter, variant in enumerate(channel_variant_ids):
            try:
                product_dict = self.prepare_individual_item_dict(channel_product_template, variant, instance, 'individual', is_publish_in_channel, is_export_or_update_price, is_export_or_update_stock)         
                results = channel_engine_obj.get_channel_product_upsert_api_object(instance, product_dict) or {}
            except Exception as e:
                if not job:
                    value = {
                            'instance_id':instance.id,
                            'message':'Export Product to channel engine.',
                            'application':'export_product',
                            'operation_type':'export',
                            'skip_process':True
                           }             
                    job = channel_log_book_obj.create(value)
                job_line_val = {
                                    'job_id':job.id,
                                    'log_type':'error',
                                    'action_type':'skip_line',
                                    'operation_type':'export',
                                    'message':'Exception when calling ProductApi->product_create: %s\n' % (e),
                                }
                channel_log_book_line_obj.create(job_line_val)
            if not results:
                results = {}
            resp_results = results
            resp_accepted_count = resp_results.get('Content', {}).get('AcceptedCount', False)
            resp_rejected_count = resp_results.get('Content', {}).get('RejectedCount', False)
            resp_success = resp_results.get('Success', False)
            if resp_success and resp_accepted_count == len(variant):
                if (product_counter == 0): variant.channel_product_tmpl_id.write({'exported_in_channel':True})
                variant.write({'exported_in_channel':True})
                self._cr.commit()
            elif resp_rejected_count == 1:
                if not job:
                    value = {
                            'instance_id':instance.id,
                            'message':'Export Product to channel engine.',
                            'application':'export_product',
                            'operation_type':'export',
                            'skip_process':True
                           }             
                    job = channel_log_book_obj.create(value)
                job_line_val = {    
                                    'channel_order_ref':variant.name,
                                    'job_id':job.id,
                                    'log_type':'error',
                                    'action_type':'skip_line',
                                    'operation_type':'export',
                                    'message':'%s' % (str(resp_results.get('Content'))),
                                }
                channel_log_book_line_obj.create(job_line_val)
        return True

    def prepare_vartiation_item_dict(self, channel_product_template, variant, parent_merchant_product_no, instance, product_type, is_publish_in_channel, product_counter, is_export_or_update_price, is_export_or_update_stock):
        channel_product_product_obj = self.env['channel.product.product']
        product_attribute_obj = self.env['product.attribute']
        
        odoo_product_id = variant and variant.product_id or False
        prod_name = self.cleanhtml(cgi.escape(variant.get_title() or channel_product_template.get_title()))
        merchant_prod_no = variant.merchant_product_no or variant.product_id.default_code
        prod_description = self.cleanhtml(cgi.escape(variant.get_description() or channel_product_template.get_description()))
        prod_brand_name = channel_product_template.product_brand_id and channel_product_template.product_brand_id.name or '' 
        ean13 = variant.ean13 or ''
        # image_url = variant.image_url
        warehouse_id = instance.warehouse_id and instance.warehouse_id.id        
        stock = channel_product_product_obj.get_channel_product_stock(variant, warehouse_id, instance.stock_field.name)
        product_price = variant.product_id.with_context({'pricelist':instance.pricelist_id.id, 'quantity':1}).price or 1.0
        
        purchase_price = (variant.product_id.standard_price or 0.0) if variant.product_id and variant.product_id.standard_price else 0.0
        catalog_price = product_price if product_price else 0.0
        seller_ids = variant.product_id and variant.product_id.seller_ids
        manufacturer_product_number = (seller_ids[0].product_code or "") if seller_ids else ""
        category_trail = odoo_product_id.categ_id.name_get()[0][1] if (odoo_product_id and odoo_product_id.categ_id) else ""

        product_size = ''
        product_color = ''
        product_dict = {}

        extra_datas = []   
        for attribute_line_id  in variant.product_id.attribute_line_ids:
            attribute_name = attribute_line_id.attribute_id.name
            for attribute_value in attribute_line_id.value_ids:
                values = attribute_value.name
                extra_data = {"key":attribute_name, "Value":values, "Type": "TEXT", "IsPublic": True}
                extra_datas.append(extra_data)
        
        if product_counter == 0:            
            product_dict_vals = {
                'MerchantProductNo' : str(merchant_prod_no),
                'Name' :prod_name ,
                'Description' : prod_description ,
                'Brand' :prod_brand_name,
                'ManufacturerProductNumber':manufacturer_product_number,
                'Stock' : int(stock) ,
                'Price' : product_price,
                'MSRP':catalog_price,
                'PurchasePrice': purchase_price,
                # 'ImageUrl' : image_url,
                "ExtraData":extra_datas,
            }
        else:
            product_dict_vals = {
                'MerchantProductNo' : str(merchant_prod_no),
                'ParentMerchantProductNo': parent_merchant_product_no,
                'Name' :prod_name ,
                'Description' : prod_description ,
                'Brand' :prod_brand_name,
                'ManufacturerProductNumber':manufacturer_product_number,
                'Stock' : int(stock)  ,
                'Price' : product_price,
                'MSRP':catalog_price,
                'PurchasePrice': purchase_price,
                # 'ImageUrl' : image_url,
                'ExtraData':extra_datas,
            }
        
        ean13 and product_dict_vals.update({'Ean' : ean13})
        product_dict = [product_dict_vals]
        # Prepare Image Dictionary
        if instance.use_website_images_or_ce_images:
            image_ids = variant.product_id.product_template_image_ids
            if variant.product_id.image:
                image_url_erpify = variant.product_id.main_image_url
                product_dict[0].update({'ImageUrl': image_url_erpify})
            image_url_kyes = [
                'ExtraImageUrl1', 'ExtraImageUrl2', 'ExtraImageUrl3',
                'ExtraImageUrl4', 'ExtraImageUrl5', 'ExtraImageUrl6',
                'ExtraImageUrl7', 'ExtraImageUrl8', 'ExtraImageUrl9'
            ]
            for image_counter, image_id in enumerate(image_ids, 0):
                if image_counter == len(image_url_kyes):
                    break
                if not image_id.image_url:  # image_id.ce_image_url:
                    continue
                product_dict[0].update({
                    image_url_kyes[image_counter]: image_id.image_url or ''
                })
        else:
            image_ids = variant.ce_product_image_ids
            image_url_kyes = [
                'ImageUrl', 'ExtraImageUrl1', 'ExtraImageUrl2', 'ExtraImageUrl3',
                'ExtraImageUrl4', 'ExtraImageUrl5', 'ExtraImageUrl6',
                'ExtraImageUrl7', 'ExtraImageUrl8', 'ExtraImageUrl9'
            ]
            for image_counter, image_id in enumerate(image_ids, 0):
                if image_counter == len(image_url_kyes):
                    break
                if not image_id.ce_image_url:
                    continue
                product_dict[0].update({
                    image_url_kyes[image_counter]: image_id.ce_image_url or ''
                })
        e_data = variant.get_translated_data()
        if instance.use_product_or_variants:
            for f in instance.prod_extra_fields_erpify:
                e_data.append(
                    {"key": f.field_description, "Value": variant.product_id[f.name], "Type": "TEXT", "IsPublic": True})
        else:
            for f in instance.prod_temp_extra_fields_erpify:
                e_data.append({"key": f.field_description, "Value": channel_product_template.product_tmpl_id[f.name],
                               "Type": "TEXT", "IsPublic": True})
        product_dict[0].update({'ExtraData': product_dict.get('ExtraData', []) + e_data})
        return product_dict or {}

    def create_variation_item(self, channel_product_template, instance, is_publish_in_channel, is_export_or_update_price, is_export_or_update_stock):
        channel_log_book_obj = self.env['channel.log.book']
        channel_log_book_line_obj = self.env['channel.log.book.line']
        channel_engine_obj = ChannelEngine()
        channel_variant_ids = channel_product_template.channel_variant_ids
        results = False
        parent_merchant_product_no = ''
        job = False
         
        for product_counter, variant in enumerate(channel_variant_ids):
            try:
                if product_counter == 0: parent_merchant_product_no = variant.merchant_product_no  
                product_dict = self.prepare_vartiation_item_dict(channel_product_template, variant, parent_merchant_product_no, instance, 'variation', is_publish_in_channel, product_counter, is_export_or_update_price, is_export_or_update_stock)
                results = channel_engine_obj.get_channel_product_upsert_api_object(instance, product_dict) or {}               
            except Exception as e:
                if not job:
                    value = {
                            'instance_id':instance.id,
                            'message':'Export Product to channel engine.',
                            'application':'export_product',
                            'operation_type':'export',
                            'skip_process':True
                           }             
                    job = channel_log_book_obj.create(value)
                job_line_val = {
                                    'job_id':job.id,
                                    'log_type':'error',
                                    'action_type':'skip_line',
                                    'operation_type':'export',
                                    'message':'Exception when calling ProductApi->product_create: %s\n' % (e),
                                }
                channel_log_book_line_obj.create(job_line_val)
            if not results:
                results = {}
            resp_results = results
            resp_accepted_count = resp_results.get('Content').get('AcceptedCount')
            resp_rejected_count = resp_results.get('Content').get('RejectedCount')
            resp_success = resp_results.get('Success', False)
            if resp_success and resp_accepted_count == len(variant):
                if (product_counter == 0): variant.channel_product_tmpl_id.write({'exported_in_channel':True})
                variant.write({'exported_in_channel':True})
                self._cr.commit()
            elif resp_rejected_count == 1:
                if not job:
                    value = {
                            'instance_id':instance.id,
                            'message':'Export Product to channel engine.',
                            'application':'export_product',
                            'operation_type':'export',
                            'skip_process':True
                           }             
                    job = channel_log_book_obj.create(value)
                
                job_line_val = {    
                                    'channel_order_ref':variant.name,
                                    'job_id':job.id,
                                    'log_type':'error',
                                    'action_type':'skip_line',
                                    'operation_type':'export',
                                    'message':'%s' % (str(resp_results.get('Content'))),
                                }
                channel_log_book_line_obj.create(job_line_val)
        return True

    def update_individual_item(self, instance, channel_product_template):
        channel_log_book_obj = self.env['channel.log.book']
        channel_log_book_line_obj = self.env['channel.log.book.line']
        channel_engine_obj = ChannelEngine()
        channel_variant_ids = channel_product_template.channel_variant_ids
        results = False
        job = False
        
        for product_counter, variant in enumerate(channel_variant_ids, 0):
            try:
                product_dict = self.prepare_individual_item_dict(channel_product_template, variant, instance, 'individual', True, True, True)
                results = channel_engine_obj.get_channel_product_upsert_api_object(instance, product_dict) or {}
            except Exception as e:
                if not job:
                    value = {
                            'instance_id':instance.id,
                            'message':'Update Product to channel engine.',
                            'application':'update_product',
                            'operation_type':'export',
                            'skip_process':True
                           }             
                    job = channel_log_book_obj.create(value)
                job_line_val = {
                                    'record_id': int(product_counter),
                                    'job_id':job.id,
                                    'log_type':'error',
                                    'action_type':'skip_line',
                                    'operation_type':'export',
                                    'message':'Exception when calling ProductApi->product_create(Update Product Time): %s\n' % (e),
                                }
                channel_log_book_line_obj.create(job_line_val)
            
            if results:
                resp_results = results
                resp_accepted_count = resp_results.get('Content').get('AcceptedCount')
                resp_rejected_count = resp_results.get('Content').get('RejectedCount')
                resp_success = resp_results.get('Success', False)
                if resp_success and resp_accepted_count == len(variant):
                    if (product_counter == 0): 
                        variant.channel_product_tmpl_id.write({'exported_in_channel':True})
                    variant.write({'exported_in_channel':True})
                    self._cr.commit()
                elif resp_rejected_count == 1:
                    if not job:
                        value = {
                                'instance_id':instance.id,
                                'message':'Update Product to channel engine.',
                                'application':'update_product',
                                'operation_type':'export',
                                'skip_process':True
                               }             
                        job = channel_log_book_obj.create(value)
                    job_line_val = {    
                                        'record_id': int(product_counter),
                                        'channel_order_ref':variant.name,
                                        'job_id':job.id,
                                        'log_type':'error',
                                        'action_type':'skip_line',
                                        'operation_type':'export',
                                        'message':'%s' % (str(resp_results.get('content'))),
                                    }
                    channel_log_book_line_obj.create(job_line_val)
        return True

    def update_variation_item(self, instance, channel_product_template):
        channel_log_book_obj = self.env['channel.log.book']
        channel_log_book_line_obj = self.env['channel.log.book.line']
        channel_engine_obj = ChannelEngine()
        channel_variant_ids = channel_product_template.channel_variant_ids
        results = False
        parent_merchant_product_no = ''
        job = False
        
        for product_counter, variant in enumerate(channel_variant_ids, 0):
            try:
                if product_counter == 0: parent_merchant_product_no = variant.merchant_product_no                
                product_dict = self.prepare_vartiation_item_dict(channel_product_template, variant, parent_merchant_product_no, instance, 'variation', True, product_counter, True, True)
                results = channel_engine_obj.get_channel_product_upsert_api_object(instance, product_dict) or {}                
            except Exception as e:
                if not job:
                    value = {
                            'instance_id':instance.id,
                            'message':'Update Product to channel engine.',
                            'application':'update_product',
                            'operation_type':'export',
                            'skip_process':True
                           }             
                    job = channel_log_book_obj.create(value)
                job_line_val = {
                                    'record_id': int(product_counter),
                                    'job_id':job.id,
                                    'log_type':'error',
                                    'action_type':'skip_line',
                                    'operation_type':'export',
                                    'message':'Exception when calling ProductApi->product_create(Update Product Time): %s\n' % (e),
                                }
                channel_log_book_line_obj.create(job_line_val)
                
            if results:
                resp_results = results
                resp_accepted_count = resp_results.get('Content').get('AcceptedCount')
                resp_rejected_count = resp_results.get('Content').get('RejectedCount')
                resp_success = resp_results.get('Success', False)
                if resp_success and resp_accepted_count == len(variant):
                    if (product_counter == 0): 
                        variant.channel_product_tmpl_id.write({'exported_in_channel':True})
                    variant.write({'exported_in_channel':True})
                    self._cr.commit()
                elif resp_rejected_count == 1:
                    if not job:
                        value = {
                                'instance_id':instance.id,
                                'message':'Update Product to channel engine.',
                                'application':'update_product',
                                'operation_type':'export',
                                'skip_process':True
                               }             
                        job = channel_log_book_obj.create(value)
                    job_line_val = {    
                                        'record_id': int(product_counter),
                                        'channel_order_ref':variant.name,
                                        'job_id':job.id,
                                        'log_type':'error',
                                        'action_type':'skip_line',
                                        'operation_type':'export',
                                        'message':'%s' % (str(resp_results.get('content'))),
                                    }
                    channel_log_book_line_obj.create(job_line_val)
        return True
    
#     @api.multi
#     def value_to_html(self, value, options=None):
#         """ value_to_html(value, field, options=None)
# 
#         Converts a single value to its HTML version/output
#         :rtype: unicode
#         """
#         return html_escape(pycompat.to_text(value))

    def create_or_update_channel_products(self, instance, final_result_contents):
        if not instance or not final_result_contents:
            return True
        
        channel_product_product_obj = self.env['channel.product.product']
        channel_product_brand_obj = self.env['channel.product.brand']
        channel_log_book_obj = self.env['channel.log.book']
        channel_log_book_line_obj = self.env['channel.log.book.line']
        product_product_obj = self.env['product.product']
        channel_process_import_export_obj = self.env['channel.process.import.export']
        
        job = False
        for resp_product_counter, resp_product_dict in enumerate(final_result_contents, 1):
            merchant_product_no = resp_product_dict.get('MerchantProductNo', '')
            product_name = resp_product_dict.get('Name', '')
            channel_product_id = channel_product_product_obj.search([('merchant_product_no', '=', merchant_product_no)], limit=1)
            
            if not channel_product_id:
                odoo_product_id = product_product_obj.search([('default_code', '=', merchant_product_no), ('type', '=', 'product')], limit=1)
                if odoo_product_id:
                    channel_process_import_export_id = channel_process_import_export_obj.with_context({'default_instance_ids': instance}).create({})
                    channel_process_import_export_id.with_context({'active_ids': odoo_product_id.product_tmpl_id.ids}).prepare_product_for_export()
                    channel_product_id = channel_product_product_obj.search([('merchant_product_no', '=', merchant_product_no)], limit=1)
                else:
                    if not job:
                        value = {
                            'instance_id': instance.id,
                            'message': 'Product not found in Odoo.',
                            'application': 'import_product',
                            'operation_type': 'import',
                            'skip_process': True
                        }             
                        job = channel_log_book_obj.create(value)
                        job_line_val = {
                            'record_id': int(resp_product_counter),
                            'channel_order_ref': merchant_product_no,
                            'job_id': job.id,
                            'log_type': 'error',
                            'action_type': 'skip_line',
                            'operation_type': 'import',
                            'message': 'Product (MerchantProductNo: %s, Name: %s) not found in Odoo.' % (merchant_product_no, product_name),
                        }
                        channel_log_book_line_obj.create(job_line_val)
                    continue
            
            if channel_product_id:
                product_description = resp_product_dict.get('Description', '')
                product_brand = resp_product_dict.get('Brand', '')
                product_isactive = resp_product_dict.get('IsActive', False)
                vals = {
                    'name': product_name,
                    # 'description': self.value_to_html(product_description,None),
                    'exported_in_channel': True,
                    'is_active_in_channel': product_isactive
                }
                channel_product_id.write(vals)
                
                brand_id = channel_product_brand_obj.search([('name', '=ilike', product_brand)], limit=1)
                if not brand_id:
                    brand_id = channel_product_brand_obj.create({'name': product_brand})
                prod_tmpl_vals = {
                    'product_brand_id': brand_id.id,
                    'exported_in_channel': True
                }
                channel_product_id.channel_product_tmpl_id.write(prod_tmpl_vals)
            else:
                if not job:
                    value = {
                        'instance_id': instance.id,
                        'message': 'Product not found in Odoo channel engine.',
                        'application': 'import_product',
                        'operation_type': 'import',
                        'skip_process': True
                    }             
                    job = channel_log_book_obj.create(value)
                job_line_val = {
                    'record_id': int(resp_product_counter),
                    'channel_order_ref': merchant_product_no,
                    'job_id': job.id,
                    'log_type': 'error',
                    'action_type': 'skip_line',
                    'operation_type': 'import',
                    'message': 'Product (MerchantProductNo: %s, Name: %s) not found in Odoo channel engine. ' % (merchant_product_no, product_name),
                }
                channel_log_book_line_obj.create(job_line_val)
        return True

    def import_products_from_channel_engine(self, channel_instances):
        channel_log_book_obj = self.env['channel.log.book']
        channel_log_book_line_obj = self.env['channel.log.book.line']
        channel_engine_obj = ChannelEngine()
        
        for instance_counter, instance in enumerate(channel_instances, 0):
            job = False
            results = False
            try:
                results = channel_engine_obj.get_channel_products_object(instance) or {}                
            except Exception as e:
                if not job:
                    value = {
                        'instance_id': instance.id,
                        'message': 'Import products from channel engine API call time getting error.',
                        'application': 'import_product',
                        'operation_type': 'import',
                        'skip_process': True
                    }             
                    job = channel_log_book_obj.create(value)
                job_line_val = {
                    'record_id': int(instance_counter),
                    'job_id': job.id,
                    'log_type': 'error',
                    'action_type': 'skip_line',
                    'operation_type': 'import',
                    'message': 'Exception when calling ProductApi->get_products(Import Products Time): %s\n' % (e),
                }
                channel_log_book_line_obj.create(job_line_val)
            if results:
                total_count = results.get('TotalCount', 0)
                resp_success = results.get('Success', False)
                final_result_contents = results.get('Content', [])    
                
                if total_count > 0 and resp_success and final_result_contents:
                    self.create_or_update_channel_products(instance, final_result_contents)
        return True
