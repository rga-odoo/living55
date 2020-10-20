# -*- coding: utf-8 -*-
import base64, json, requests, time
from odoo import models, fields, api, _
from odoo.addons.channel_engine.channel_engine_api.api import ChannelEngine
from odoo.exceptions import Warning


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_channel_order_status(self):
        for order in self:
            if order.picking_ids:
                order.is_order_updated_in_channel = True
            else:
                order.is_order_updated_in_channel = False
            for picking in order.picking_ids:
                if picking.state == 'cancel' or picking.picking_type_id.code != 'outgoing':
                    continue
                if not picking.is_updated_in_channel:
                    order.is_order_updated_in_channel = False
                    break

    channel_order_no = fields.Char(string='Channel Order No', size=50, help="Channel order no.")
    channel_order_id = fields.Char(string='Channel Order Id', size=50, help="Channel order id")
    channel_name = fields.Char('Channel Name', help="Channel Name")
    merchant_order_no = fields.Char(string='Merchant Order No', size=50, help="Merchant Order No.")
    merchant_shipment_no = fields.Char(string='Merchant Shipment No', size=50, help="Merchant shipment no.")
    instance_id = fields.Many2one('ce.instance', string='Channel Instance', help="Channel instance name")
    is_send_acknowledge_order = fields.Boolean(string='Send Order Acknowledge ?', default=False,
                                               help="True if already send Order Acknowledge other wise False. By default set False.")
    is_order_updated_in_channel = fields.Boolean(string='Order Updated In CE ?', compute="_get_channel_order_status",
                                                 search="_search_ce_order_ids",
                                                 help="Sale order updated in channel engine? True if yes other wise False")
    is_already_download_packing_slip = fields.Boolean(string="Is Downloaded Order Packing Slip ?", default=False,
                                                      copy=False, help="Downloaded packing slip for this order.")

    def _search_ce_order_ids(self, operator, value):
        query = """
            select sale_order.id from stock_picking
            inner join sale_order on sale_order.id=stock_picking.sale_id and sale_order.channel_order_no is not null
            inner join stock_location on stock_location.id=stock_picking.location_dest_id and (stock_location.usage='customer')
            where stock_picking.is_updated_in_channel=False and stock_picking.state='done';    
        """
        self._cr.execute(query)
        results = self._cr.fetchall()
        order_ids = []
        for result_tuple in results:
            order_ids.append(result_tuple[0])
        return [('id', 'in', order_ids)]

    def _get_map_order_status(self, instance, order_dict):
        channel_order_status = order_dict.get('Status', '')
        if channel_order_status:
            if channel_order_status == 'NEW':
                channel_order_status = 'draft'
            elif channel_order_status == 'IN_PROGRESS':
                channel_order_status = 'draft'
        else:
            channel_order_status = 'draft'
        return channel_order_status

    def channel_order_validation_details_check(self, instance, order_dict):
        channel_log_book_obj = self.env['channel.log.book']
        channel_log_book_line_obj = self.env['channel.log.book.line']
        channel_product_product_obj = self.env['channel.product.product']
        odoo_product_obj = self.env['product.product']
        channel_marketplace_name_object = self.env['ce.name']
        channel_sale_auto_workflow_obj = self.env['ce.sale.auto.workflow.configuration']
        channel_order_no = order_dict.get('ChannelOrderNo', '')
        job = False
        skip_process = False
        log_message = ''
        operation_type = ''
        log_line_message = ''
        log_type = ''
        
        # Order validations
        channel_status = order_dict.get('Status', '')
        channel_name = order_dict.get('ChannelName', '')
        print(channel_name)
        channel_marketplace_name_id = channel_marketplace_name_object.search([('name', '=', channel_name)], limit=1)
        if not channel_marketplace_name_id:
            if not job:
                value = {
                    'instance_id': instance.id,
                    'message': "Order not imported due to not found Channel Name.",
                    'application': 'import_sales_orders',
                    'operation_type': 'import',
                    'skip_process': True
                }
                job = channel_log_book_obj.create(value)
            job_line_val = {
                'job_id': job.id,
                'channel_order_ref': channel_order_no,
                'log_type': 'not_found',
                'action_type': 'skip_line',
                'operation_type': 'import',
                'message': "Not found Channel Name '%s' inside Odoo Channel Engine so First create Channel Name '%s' then Import Order." % (channel_name, channel_name)
            }
            channel_log_book_line_obj.create(job_line_val)
            return job, True
        
        
        channel_workflow_record = channel_sale_auto_workflow_obj.search(
            [('instance_id', '=', instance.id), ('channel_id', '=', channel_marketplace_name_id.id),
             ('channel_order_status', '=', channel_status)], limit=1)
        if not channel_workflow_record:
            if not job:
                value = {
                    'instance_id': instance.id,
                    'message': "Order not imported due to not found Channel Order Status(Order workflow) Channel.",
                    'application': 'import_sales_orders',
                    'operation_type': 'import',
                    'skip_process': True
                }
                job = channel_log_book_obj.create(value)
            job_line_val = {
                'job_id': job.id,
                'channel_order_ref': channel_order_no,
                'log_type': 'not_found',
                'action_type': 'skip_line',
                'operation_type': 'import',
                'message': "Not found Channel Order Status Workflow for '%s' Status inside Odoo Channel Engine so First create Channel Order Status Workflow for '%s' Status then Import Order." % (channel_name, channel_name)
            }
            channel_log_book_line_obj.create(job_line_val)
            return job, True
        
        
        # Order lines validations
        order_lines = order_dict.get('Lines', [])
        for order_line in order_lines:
            merchant_product_no = order_line.get('MerchantProductNo', '')
            if merchant_product_no:
                channel_product = channel_product_product_obj.search(
                    [('instance_id', '=', instance.id), ('merchant_product_no', '=', merchant_product_no)], limit=1)
                if channel_product:
                    continue
                else:
                    odoo_project = odoo_product_obj.search([('default_code', '=', merchant_product_no)], limit=1)
                    if odoo_project or (odoo_project and not odoo_project.active):
                        odoo_project.write({'active': True})
                        continue
                    else:
                        skip_process = True
                        log_message = 'Order is not imported due to product not found issue.'
                        operation_type = 'import'
                        action_type = 'skip_line'
                        log_line_message = 'Product %s not found for %s instance' % (merchant_product_no, instance.name)
                        log_type = 'not_found'
            else:
                skip_process = True
                log_message = 'Order is not imported due to product Merchant Product No found Null.'
                operation_type = 'import'
                action_type = 'skip_line'
                log_line_message = 'Product Merchant Product No null found for %s instance' % (instance.name)
                log_type = 'not_found'

            if not job:
                value = {
                    'instance_id': instance.id,
                    'message': log_message,
                    'application': 'import_sales_orders',
                    'operation_type': operation_type,
                    'skip_process': skip_process
                }
                job = channel_log_book_obj.create(value)
            job_line_val = {
                'job_id': job.id,
                'channel_order_ref': channel_order_no,
                'log_type': log_type,
                'action_type': action_type,
                'operation_type': operation_type,
                'message': log_line_message
            }
            channel_log_book_line_obj.create(job_line_val)

        return job, skip_process

    def create_channel_sales_order_dict(self, instance, order_dict, partner_vals_dict):
        sale_order_obj = self.env['sale.order']
        channel_payment_options_obj = self.env['channel.payment.options']
        channel_sale_auto_workflow_obj = self.env['ce.sale.auto.workflow.configuration']
        channel_marketplace_name_object = self.env['ce.name']

        channel_payment_method = order_dict.get('PaymentMethod', '')
        company_id = instance.company_id and instance.company_id.id or False
        partner_id = partner_vals_dict.get('invoice_address')
        partner_invoice_id = partner_vals_dict.get('invoice_address')
        partner_shipping_id = partner_vals_dict.get('delivery_address')
        channel_status = order_dict.get('Status', '')
        channel_name = order_dict.get('ChannelName', '')

        channel_marketplace_name_id = channel_marketplace_name_object.search([('name', '=', channel_name)], limit=1)
        channel_workflow_record = channel_sale_auto_workflow_obj.search(
            [('instance_id', '=', instance.id), ('channel_id', '=', channel_marketplace_name_id.id),
             ('channel_order_status', '=', channel_status)], limit=1)
        sale_auto_workflow = channel_workflow_record.auto_workflow_id

        order_vals = {
            'company_id': company_id,
            'partner_id': partner_id,
            'partner_invoice_id': partner_invoice_id,
            'partner_shipping_id': partner_shipping_id,
            'warehouse_id': instance.warehouse_id and instance.warehouse_id.id or False,
            'state': self._get_map_order_status(instance, order_dict),
        }
        # new_record = sale_order_obj.new(order_vals)
        # new_record.onchange_partner_id()
        # order_vals = sale_order_obj._convert_to_write({name: new_record[name] for name in new_record._cache})
        #
        # new_record = sale_order_obj.new(order_vals)
        # #new_record.onchange_delivery_id(company_id, partner_id, partner_shipping_id, fiscal_position)
        # order_vals = sale_order_obj._convert_to_write({name: new_record[name] for name in new_record._cache})

        payment_option_id = channel_payment_options_obj.search(
            [('name', '=', channel_payment_method), ('instance_id', '=', instance.id)], limit=1)
        order_vals.update({
            'name': "%s%s" % (instance.order_prefix or '', order_dict.get('ChannelOrderNo', '')),
            'date_order': instance.openerp_format_date(order_dict.get('OrderDate', False)) or False,
            'instance_id': instance.id or False,
            'team_id': instance.team_id and instance.team_id.id or False,
            'partner_invoice_id': partner_vals_dict.get('invoice_address'),
            'partner_shipping_id': partner_vals_dict.get('delivery_address'),
            'pricelist_id': partner_vals_dict.get('pricelist_id'),
            'channel_order_no': order_dict.get('ChannelOrderNo', ''),
            'channel_order_id': order_dict.get('Id', ''),
            'merchant_order_no': order_dict.get('ChannelOrderNo', ''),
            'channel_name': order_dict.get('ChannelName', ''),
            'picking_policy': sale_auto_workflow.picking_policy,
            'auto_workflow_process_id': sale_auto_workflow.id,
            'payment_term_id': instance.payment_term_id.id if instance.payment_term_id else False,
            'user_id': instance.user_id_erpify.id,
            'fiscal_position_id': channel_marketplace_name_id.fiscal_position_id.id if channel_marketplace_name_id.fiscal_position_id else False,
        })
        return order_vals

    def create_or_update_channel_partner(self, instance, order_dict):
        res_partner_obj = self.env['res.partner']
        res_country_obj = self.env['res.country']
        partner_vals_dict = {}
        partner = False

        # partner_id = instance.partner_id.id if instance.partner_id else False
        shipping_address = order_dict.get('ShippingAddress', {})
        country_id = res_country_obj.search([('code', '=', shipping_address.get('CountryIso', ''))], limit=1)
        zip_code = shipping_address.get('ZipCode', '')
        first_name = shipping_address.get('FirstName', '')
        last_name = shipping_address.get('LastName', '')
        customer_name = (first_name + " " + last_name) if (first_name and last_name) else 'Channel Engine Customer'
        channel_customer_no = order_dict.get('ChannelCustomerNo', '')
        city = shipping_address.get('City', '')
        street = shipping_address.get('StreetName', '')
        email_id = order_dict.get('Email', '')
        phone = order_dict.get('Phone', '')

        partner_vals = {
            'is_company': False, 'customer_rank': 1,
            'lang': instance.lang_id and instance.lang_id.code,
            'country_id': country_id and country_id.id or False,
            'zip': zip_code,
            'city': city,
            'street': street,
            'email': email_id,
            'phone': phone
        }
        if instance.pricelist_id:
            partner_vals.update({'property_product_pricelist': instance.pricelist_id.id or False})

        exist_ce_partner = res_partner_obj.search(
            [('channel_customer_no', '=', True), ('channel_customer_no', '=', channel_customer_no)], limit=1)
        _domain = []
        # street and _domain.append(('street','=',street))
        # city and _domain.append(('city','=',city))
        # zip_code and _domain.append(('zip','=',zip_code))
        # country_id and _domain.append(('country_id','=',country_id.id))
        # customer_name and _domain.append(('name','=',customer_name))
        email_id and _domain.append(('email', '=', email_id))
        phone and _domain.append(('phone', '=', phone))
        exist_odoo_partner = res_partner_obj.search(_domain + [('type', '=', 'delivery')])
        if not exist_odoo_partner:
            partner_byemail = res_partner_obj.search([('email', '=', email_id), ('type', '=', 'delivery')])
            if partner_byemail:
                exist_odoo_partner = partner_byemail
        if exist_ce_partner or exist_odoo_partner:
            if exist_odoo_partner and len(exist_odoo_partner) == 1:
                partner_vals_dict.update(
                    {'invoice_address': exist_odoo_partner.id, 'delivery_address': exist_odoo_partner.id,
                     'pricelist_id': exist_odoo_partner.property_product_pricelist and exist_odoo_partner.property_product_pricelist.id})
                return exist_odoo_partner, partner_vals_dict
            elif exist_ce_partner:
                partner_vals_dict.update(
                    {'invoice_address': exist_ce_partner.id, 'delivery_address': exist_ce_partner.id,
                     'pricelist_id': exist_ce_partner.property_product_pricelist and exist_ce_partner.property_product_pricelist.id})
                return exist_ce_partner, partner_vals_dict
            else:
                partner_vals.update({
                    'name': customer_name,
                    'type': 'delivery',
                    'channel_customer_no': channel_customer_no,
                    # 'parent_id': exist_ce_partner.id
                })
                partner = res_partner_obj.create(partner_vals)
                partner and partner_vals_dict.update(({'invoice_address': partner.id, 'delivery_address': partner.id,
                                                       'pricelist_id': partner.property_product_pricelist and partner.property_product_pricelist.id}))
                return partner, partner_vals_dict
        else:
            partner_vals.update({
                'name': customer_name,
                'type': 'delivery',
                'channel_customer_no': channel_customer_no
            })
            partner = res_partner_obj.create(partner_vals)
            partner and partner_vals_dict.update(({'invoice_address': partner.id, 'delivery_address': partner.id,
                                                   'pricelist_id': partner.property_product_pricelist and partner.property_product_pricelist.id}))
        return partner, partner_vals_dict

    def create_channel_sales_order(self, instance, orders_list):
        channel_log_book_obj = self.env['channel.log.book']
        channel_log_book_line_obj = self.env['channel.log.book.line']
        sale_order_line_obj = self.env['sale.order.line']
        sale_auto_workflow_process_obj = self.env['sale.workflow.process.ept']

        import_order_ids = []
        job = False
        for order_dict in orders_list:
            channel_order_no = order_dict.get('ChannelOrderNo', '')
            order_line_status = self._get_map_order_status(instance, order_dict)
            shipping_cost_incl_vat = order_dict.get('ShippingCostsInclVat', 0.0)

            exist_order_id = self.search(
                [('channel_order_no', '=', channel_order_no), ('instance_id', '=', instance.id)], limit=1)
            if exist_order_id:
                continue

            job, skip_process = self.channel_order_validation_details_check(instance, order_dict)
            if skip_process:
                continue

            partner, partner_vals_dict = self.create_or_update_channel_partner(instance, order_dict)
            if not partner:
                if not job:
                    value = {
                        'instance_id': instance.id,
                        'message': 'Import Sales Orders From Channel Engine.',
                        'application': 'import_sales_orders',
                        'operation_type': 'import',
                        'skip_process': True
                    }
                    job = channel_log_book_obj.create(value)
                job_line_val = {
                    'job_id': job.id,
                    'channel_order_ref': channel_order_no,
                    'log_type': 'not_found',
                    'action_type': 'skip_line',
                    'operation_type': 'import',
                    'message': "Customer Not Available In %s Order." % (channel_order_no)
                }
                channel_log_book_line_obj.create(job_line_val)

            order_vals_dict = self.create_channel_sales_order_dict(instance, order_dict, partner_vals_dict)
            channel_order = self.create(order_vals_dict) if order_vals_dict else False
            if not channel_order:
                continue
            import_order_ids.append(channel_order)

            is_already_shipment_line = False
            if float(shipping_cost_incl_vat) > 0.0:
                is_already_shipment_line = True
                shipment_charge_product = instance.shipment_charge_product_id
                shipment_charge_product_name = shipment_charge_product and shipment_charge_product.name or 'ShippingCostsInclVat'
                order_line_vals_dict = sale_order_line_obj.create_channel_sale_order_line_dict(instance, {},
                                                                                               shipping_cost_incl_vat,
                                                                                               False,
                                                                                               shipment_charge_product,
                                                                                               channel_order,
                                                                                               shipment_charge_product_name,
                                                                                               partner,
                                                                                               partner_vals_dict,
                                                                                               order_line_status)
                order_line_vals_dict.update({'is_delivery': True})
                if order_line_vals_dict:
                    sale_order_line_obj.create(order_line_vals_dict)
            sale_order_line_obj.create_channel_sale_order_line(instance, channel_order, order_dict, partner,
                                                               partner_vals_dict, is_already_shipment_line)
            sale_auto_workflow_process_obj.auto_workflow_process(channel_order.auto_workflow_process_id.id,
                                                                 channel_order.ids)
        return True

    def import_sales_order_from_channel(self, instance):
        channel_log_book_obj = self.env['channel.log.book']
        channel_log_book_line_obj = self.env['channel.log.book.line']
        channel_sale_auto_workflow_config_obj = self.env['ce.sale.auto.workflow.configuration']
        channel_engine_obj = ChannelEngine()
        channel_sale_auto_workflow_config_ids = channel_sale_auto_workflow_config_obj.search(
            [('instance_id', '=', instance.id)])

        filter_statuses = [x.channel_order_status for x in channel_sale_auto_workflow_config_ids]
        # filter_statuses = ['IN_PROGRESS']

        filter_fulfillment_type = 'ALL'
        filter_page = ''
        results = {}
        job = False

        try:
            results = channel_engine_obj.get_channel_order_by_filter_api_object(instance, filter_statuses,
                                                                                filter_fulfillment_type,
                                                                                filter_page) or {}
        except Exception as e:
            if not job:
                value = {
                    'instance_id': instance.id,
                    'message': 'Import Sales Orders From Channel Engine',
                    'application': 'import_sales_orders',
                    'operation_type': 'import',
                    'skip_process': True
                }
                job = channel_log_book_obj.create(value)
            job_line_val = {
                'job_id': job.id,
                'log_type': 'error',
                'action_type': 'skip_line',
                'operation_type': 'import',
                'message': 'Exception when calling OrderApi->order_get_by_filter: %s\n' % (e),
            }
            channel_log_book_line_obj.create(job_line_val)
        if results:
            total_count = results.get('TotalCount', 0)
            resp_success = results.get('Success', False)
            resp_content = results.get('Content', [])

            if total_count > 0 and resp_success and resp_content:
                self.create_channel_sales_order(instance, resp_content)
        return True

    def send_order_acknowledge_in_channel(self, instance, sale_orders):
        channel_log_book_obj = self.env['channel.log.book']
        channel_log_book_line_obj = self.env['channel.log.book.line']
        channel_engine_obj = ChannelEngine()
        job = False
        results = {}

        for order_counter, sale_order in enumerate(sale_orders, 1):
            try:
                channel_order_id = sale_order.channel_order_id
                merchant_order_no = sale_order.merchant_order_no
                data = {
                    "OrderId": int(channel_order_id),
                    "MerchantOrderNo": str(merchant_order_no),
                }
                results = channel_engine_obj.get_channel_acknowledge_order_api_object(instance, data) or {}
            except Exception as e:
                if not job:
                    value = {
                        'instance_id': instance.id,
                        'message': '%s' % str(results.get('Message')) or 'Send Order Acknowledge in Channel Engine.',
                        'application': 'send_order_ack',
                        'operation_type': 'export',
                        'skip_process': True
                    }
                    job = channel_log_book_obj.create(value)
                job_line_val = {
                    'job_id': job.id,
                    'log_type': 'error',
                    'action_type': 'skip_line',
                    'operation_type': 'export',
                    'message': 'Exception when calling OrderApi->order_acknowledge: %s\n' % (e),
                }
                channel_log_book_line_obj.create(job_line_val)

            if results:
                resp_success = results.get('Success', False)
                resp_status_code = results.get('StatusCode')

                if resp_status_code == 201 and resp_success:
                    sale_order.write({'is_send_acknowledge_order': True})
                elif (resp_status_code != 201 or resp_status_code in [404, 409]) and (not resp_success):
                    if resp_status_code == 409:
                        sale_order.write({'is_send_acknowledge_order': True})
                    if not job:
                        value = {
                            'instance_id': instance.id,
                            'message': '%s' % (str(results.get('Message'))),
                            'application': 'send_order_ack',
                            'operation_type': 'export',
                            'skip_process': True
                        }
                        job = channel_log_book_obj.create(value)
                    job_line_val = {
                        'record_id': int(order_counter),
                        'channel_order_ref': sale_order.name,
                        'job_id': job.id,
                        'log_type': 'error',
                        'action_type': 'skip_line',
                        'operation_type': 'export',
                        'message': '%s' % (str(results.get('Message')))
                    }
                    channel_log_book_line_obj.create(job_line_val)
        return True

    def create_shipment_in_channel(self, instance):
        channel_log_book_obj = self.env['channel.log.book']
        channel_log_book_line_obj = self.env['channel.log.book.line']
        channel_product_product_obj = self.env['channel.product.product']
        channel_engine_obj = ChannelEngine()

        _domain = [
            ('instance_id', '=', instance.id),
            ('warehouse_id', '=', instance.warehouse_id.id),
            ('channel_order_no', '!=', ""),
            ('state', 'in', ['sale', 'done']),
            ('is_order_updated_in_channel', '=', False),
            ('is_send_acknowledge_order', '=', True)
        ]
        channel_orders = self.search(_domain, order='date_order')
        if not channel_orders:
            return True

        for order_counter, channel_order in enumerate(channel_orders, 1):
            merchant_order_no = channel_order.merchant_order_no
            merchant_shipment_no = channel_order.merchant_shipment_no
            carrier_name = channel_order.picking_ids[0].carrier_id and channel_order.picking_ids[
                0].carrier_id.name or False

            not_found_channel_products_list = []
            tracking_number_list = []
            order_lines = []
            product_qty_dict = {}
            channel_product_dict = {}
            results = False
            job = False

            picking_ids = channel_order.picking_ids.filtered(
                lambda x: x.state == 'done' and x.picking_type_code == 'outgoing' and x.is_updated_in_channel == False)
            for picking in picking_ids:
                if picking.state == 'done' and picking.carrier_tracking_ref:
                    tracking_number_list.append(picking.carrier_tracking_ref)

                if not merchant_shipment_no:
                    merchant_shipment_no = picking.name
                
                # Non kit type products
                non_kit_moves = picking.move_lines.filtered(lambda x: x.sale_line_id.product_id.id == x.product_id.id and x.state == 'done')
                for move in non_kit_moves:
                    product = move.product_id
                    channel_product = False
                    if product in channel_product_dict.keys():
                        channel_product = channel_product_dict.get(product)
                    else:
                        channel_product = channel_product_product_obj.search([('product_id', '=', product.id)], limit=1)
                        if not channel_product:
                            not_found_channel_products_list.append(
                                {'Product Name': product.name, 'Internal Reference': product.default_code})
                            continue
                        channel_product_dict.update({product: channel_product})

                    merchant_product_no = channel_product and channel_product.merchant_product_no
                    qty = product_qty_dict.get(merchant_product_no, 0.0)
                    product_qty_dict.update({merchant_product_no: qty + move.product_qty})
                
                # Kit type products
                kit_sale_line_ids = picking.move_lines.filtered(lambda x: x.sale_line_id.product_id.id != x.product_id.id and x.state == 'done').mapped('sale_line_id')
                for sale_line in kit_sale_line_ids:
                    product = sale_line.product_id
                    channel_product = False
                    if product in channel_product_dict.keys():
                        channel_product = channel_product_dict.get(product)
                    else:
                        channel_product = channel_product_product_obj.search([('product_id', '=', product.id)], limit=1)
                        if not channel_product:
                            not_found_channel_products_list.append(
                                {'Product Name': product.name, 'Internal Reference': product.default_code})
                            continue
                        channel_product_dict.update({product: channel_product})

                    merchant_product_no = channel_product and channel_product.merchant_product_no
                    qty = product_qty_dict.get(merchant_product_no, 0.0)
                    product_qty_dict.update({merchant_product_no: qty + sale_line.product_uom_qty})

            if not_found_channel_products_list:
                not_found_order_channel_products = {
                    'Message': 'Due to not found products in odoo channel engine skip this order for create shipment in channel engine.',
                    'Order Number': channel_order.merchant_order_no,
                    'Not found CE products': not_found_channel_products_list
                }
                if not job:
                    value = {
                        'instance_id': instance.id,
                        'message': 'Due to not found products in odoo channel engine skip this order for create shipment in channel engine.',
                        'application': 'create_shipment',
                        'operation_type': 'export',
                        'skip_process': True
                    }
                    job = channel_log_book_obj.create(value)
                job_line_val = {
                    'record_id': int(order_counter),
                    'job_id': job.id,
                    'log_type': 'error',
                    'action_type': 'skip_line',
                    'operation_type': 'export',
                    'message': '%s' % (not_found_order_channel_products),
                }
                channel_log_book_line_obj.create(job_line_val)
                continue

            if not product_qty_dict:
                continue

            for merchant_product_no, qty in product_qty_dict.items():
                order_lines = order_lines + [{
                    'MerchantProductNo': merchant_product_no,
                    'Quantity': int(qty)
                }]

            try:
                data = {
                    "MerchantShipmentNo": merchant_shipment_no,
                    "MerchantOrderNo": merchant_order_no,
                    "Lines": order_lines,
                    "TrackTraceNo": tracking_number_list and tracking_number_list[0] or '',
                    "Method": carrier_name
                }
                results = channel_engine_obj.get_channel_create_shipment_api_object(instance, data) or {}
            except Exception as e:
                if not job:
                    value = {
                        'instance_id': instance.id,
                        'message': 'Create Shipment In Channel Engine.',
                        'application': 'create_shipment',
                        'operation_type': 'export',
                        'skip_process': True
                    }
                    job = channel_log_book_obj.create(value)
                job_line_val = {
                    'record_id': int(order_counter),
                    'job_id': job.id,
                    'log_type': 'error',
                    'action_type': 'skip_line',
                    'operation_type': 'export',
                    'message': 'Exception when calling ShipmentApi->shipment_create: %s\n' % (e),
                }
                channel_log_book_line_obj.create(job_line_val)

            if results:
                resp_success = results.get('Success', False)
                resp_status_code = results.get('StatusCode')
                if resp_status_code == 201 and resp_success:
                    picking_ids.write({'is_updated_in_channel': True})
                elif (resp_status_code in [400, 404, 409]) and not resp_success:
                    if resp_status_code == 409:
                        picking_ids.write({'is_updated_in_channel': True})
                    if not job:
                        value = {
                            'instance_id': instance.id,
                            'message': '%s' % (str(results.get('Message'))),
                            'application': 'create_shipment',
                            'operation_type': 'export',
                            'skip_process': True
                        }
                        job = channel_log_book_obj.create(value)
                    job_line_val = {
                        'record_id': int(order_counter),
                        'channel_order_ref': channel_order.name,
                        'job_id': job.id,
                        'log_type': 'error',
                        'action_type': 'skip_line',
                        'operation_type': 'export',
                        'message': '%s' % (str(results.get('Message')))
                    }
                    channel_log_book_line_obj.create(job_line_val)
        return True

    def action_confirm(self):
        """
            Confirm channel engine's sale order to automatically send order acknowledgement to channel engine. 
        """
        res = super(SaleOrder, self).action_confirm()
        for order in self.filtered(lambda o: o.state in ['sale', 'done'] and o.channel_order_no \
                                             and o.channel_order_id and o.merchant_order_no
                                             and not o.is_send_acknowledge_order and not o.is_order_updated_in_channel and o.instance_id and o.instance_id.is_order_confirm_to_auto_send_ack):
            order.send_order_acknowledge_in_channel(order.instance_id, order)
        return res

    def download_ce_order_packing_slip(self, instances):
        channel_log_book_obj = self.env['channel.log.book']
        channel_log_book_line_obj = self.env['channel.log.book.line']
        channel_engine_obj = ChannelEngine()

        for instance in instances:
            job = False
            results = {}
            _domain = [
                ('state', '=', 'sale'),
                ('instance_id', 'in', instance.ids),
                ('channel_order_no', '!=', ''),
                ('channel_order_id', '!=', ''),
                ('merchant_order_no', '!=', ''),
                ('is_send_acknowledge_order', '=', True),
                ('is_already_download_packing_slip', '=', False)
            ]
            sale_orders = self.search(_domain)
            if not sale_orders:
                continue

            for order_counter, sale_order in enumerate(sale_orders, 1):
                try:
                    merchant_order_no = sale_order.merchant_order_no
                    results = channel_engine_obj.download_ce_order_packing_slip(merchant_order_no, instance)
                except Exception as e:
                    if not job:
                        value = {
                            'instance_id': instance.id,
                            'message': '%s' % str(results.json().get('Message')) or 'Download order packing slip.',
                            'application': 'download_order_packing_slip',
                            'operation_type': 'import',
                            'skip_process': True
                        }
                        job = channel_log_book_obj.create(value)
                    job_line_val = {
                        'channel_order_ref': sale_order.name,
                        'job_id': job.id,
                        'log_type': 'error',
                        'action_type': 'skip_line',
                        'operation_type': 'import',
                        'message': 'Exception when calling OrderApi->Packingslip: %s\n' % (e),
                    }
                    channel_log_book_line_obj.create(job_line_val)
                    continue

                if results.status_code == 200:
                    pdf_binary_content = results.content or b''
                    binary_datas = base64.b64encode(pdf_binary_content)
                    fail_name = 'CE Packing Slip ' + time.strftime("%Y_%m_%d %H_%M_%S") + '.pdf'
                    self.env['ir.attachment'].create({
                        'name': fail_name,
                        # 'datas_fname': fail_name,
                        'datas': binary_datas,
                        'type': 'binary',
                        'res_model': sale_order._name,
                        'res_id': sale_order.id,
                        'res_name': sale_order.name,
                        'company_id': sale_order.company_id and sale_order.company_id.id or False
                    })
                    for picking in sale_order.picking_ids.filtered(lambda p: p.picking_type_code == 'outgoing'):
                        self.env['ir.attachment'].create({
                            'name': fail_name,
                            # 'datas_fname': fail_name,
                            'datas': binary_datas,
                            'type': 'binary',
                            'res_model': picking._name,
                            'res_id': picking.id,
                            'res_name': picking.name,
                            'company_id': picking.company_id and picking.company_id.id or False
                        })
                    sale_order.write({'is_already_download_packing_slip': True})
                else:
                    try:
                        results_response = results.json()
                    except Exception as e:
                        results_response = {
                            'Message': 'Due to not proper format of the MerchantOrderNumber of current order for download packing slip so,' +
                                       'You can not download packing slip for this order.'
                        }
                        pass

                    if not job:
                        value = {
                            'instance_id': instance.id,
                            'message': '%s' % 'Download order packing slip.',
                            'application': 'download_order_packing_slip',
                            'operation_type': 'import',
                            'skip_process': True
                        }
                        job = channel_log_book_obj.create(value)
                    job_line_val = {
                        'channel_order_ref': sale_order.name,
                        'job_id': job.id,
                        'log_type': 'error',
                        'action_type': 'skip_line',
                        'operation_type': 'import',
                        'message': '%s' % (results_response.get('Message')),
                    }
                    channel_log_book_line_obj.create(job_line_val)
                    continue
        return True
