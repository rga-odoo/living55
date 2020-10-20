# -*- coding: utf-8 -*-
import base64, json, requests, time
from odoo import models, fields, api, _
from odoo.addons.channel_engine.channel_engine_api.api import ChannelEngine
from odoo.exceptions import Warning


class StockPicking(models.Model):
    _inherit = "stock.picking"

    ce_instance_id = fields.Many2one('ce.instance', string='Channel Instance',
                                     compute="_check_and_set_is_channel_order", store=True, help="Channel Instance")
    is_updated_in_channel = fields.Boolean(string='Updated In Channel ?', default=False, copy=False,
                                           help="Updated in channel engine.")
    is_channel_delivery_order = fields.Boolean("Channel Delivery Order", compute="_check_and_set_is_channel_order",
                                               store=True)

    @api.depends("sale_id")
    def _check_and_set_is_channel_order(self):
        for picking in self:
            if picking.sale_id and picking.sale_id.channel_order_id:
                picking.ce_instance_id = picking.sale_id.instance_id and picking.sale_id.instance_id.id or False
                picking.is_channel_delivery_order = True

    def download_ce_dos_packing_slip(self, pickings):
        channel_log_book_obj = self.env['channel.log.book']
        channel_log_book_line_obj = self.env['channel.log.book.line']
        channel_engine_obj = ChannelEngine()

        attachment_ids = []
        for order_counter, picking in enumerate(pickings, 1):
            try:
                sale_order = picking.sale_id
                merchant_order_no = sale_order.merchant_order_no
                instance = picking.ce_instance_id
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
                    'channel_order_ref': picking.name,
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
                fail_name = 'CE Packing Slip (%s) %s%s' % (picking.name, time.strftime("%Y_%m_%d %H_%M_%S"), '.pdf')
                attachement_id = self.env['ir.attachment'].create({
                    'name': fail_name,
                   # 'datas_fname': fail_name,
                    'datas': binary_datas,
                    'type': 'binary',
                    'res_model': picking._name,
                    'res_id': picking.id,
                    'res_name': picking.name,
                    'company_id': picking.company_id and picking.company_id.id or False
                })
                attachment_ids.append(attachement_id.id)
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
                    'channel_order_ref': picking.name,
                    'job_id': job.id,
                    'log_type': 'error',
                    'action_type': 'skip_line',
                    'operation_type': 'import',
                    'message': '%s' % (results_response.get('Message')),
                }
                channel_log_book_line_obj.create(job_line_val)
                continue
        return attachment_ids
