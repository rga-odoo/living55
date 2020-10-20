# -*- coding: utf-8 -*-
from odoo import models,fields,api

class ChannelLogBook(models.Model):
    _name = "channel.log.book"
    _order = "id desc"
    _description = "Channel Log Book"
    
    name = fields.Char("Name",default="Log",index=True,help="Log Name")
    create_date = fields.Datetime("Create Date")
    instance_id = fields.Many2one('ce.instance',string="Instance")
    message = fields.Text("Message")
    operation_type = fields.Selection([('import','Import'),('export','Export')], string="Operation")
    channel_log_book_line_ids = fields.One2many("channel.log.book.line", "job_id", string="Log")
    application = fields.Selection([
        ('export_product','Export Product'),
        ('send_order_ack','Send Order Acknowledge'),
        ('update_product_stock','Update Product Stock'),
        ('update_product_price','Update Product Price'),
        ('import_sales_orders','Import Sales Orders'),
        ('create_shipment','Create Shipment'),
        ('update_product','Update Product'),
        ('import_product','Import Product'),
        ('download_order_packing_slip','Download Order Packing Slip')
    ],string="Application")
    skip_process = fields.Boolean("Skip Process")
    
    @api.model
    def create(self,vals):
        ce_log_book_seq = self.env['ir.sequence'].next_by_code('channel.log.book')
        vals.update({'name': ce_log_book_seq })
        return super(ChannelLogBook,self).create(vals)


class ChannelLogBookLine(models.Model):
    _name = 'channel.log.book.line'
    _description = "Channel Log Book Line"

    message = fields.Text("Message")
    job_id = fields.Many2one("channel.log.book",string="Job")
    operation_type = fields.Selection([('import','Import'),('export','Export')],string="Operation",related="job_id.operation_type",store=False,readonly=True)
    channel_order_ref = fields.Char("Channel Order Ref")
    create_date = fields.Datetime("Created Date")
    model_id = fields.Many2one("ir.model",string="Model")
    record_id = fields.Integer("Record ID")
    action_type = fields.Selection([
        ('create','Created New'),
        ('skip_line','Line Skipped'),
        ('terminate_process_with_log','Terminate Process With Log')], 'Action')
    log_type = fields.Selection([
        ('not_found','NOT FOUND'),
        ('mismatch','MISMATCH'),
        ('error','Error'),
        ('warning','Warning')],'Log Type')
    
    @api.model
    def get_model_id(self, model_name):
        model = self.env['ir.model'].search([('model','=',model_name)])
        if model:
            return model.id
        return False