# -*- coding: utf-8 -*-
from odoo import models, fields


class ChannelSaleAutoWorkflowConfiguration(models.Model):
    _name = "ce.sale.auto.workflow.configuration"
    _description = "Channel Engine Sale Auto Workflow Configuration"
    
    auto_workflow_id = fields.Many2one("sale.workflow.process.ept","Auto Workflow",required=True,help="Select Auto Workflow.")
    instance_id = fields.Many2one('ce.instance', string='Instance',required=True,help="Select Instance.")
    channel_id = fields.Many2one('ce.name', string='Channel Name',help="Select Channel Name.")
    channel_order_status = fields.Selection([('NEW','[NEW] The order have New status')],default="NEW",string="Sale Order Status",required=True)
    
    _sql_constraints=[
        ('_workflow_unique_constraint','unique(channel_id,auto_workflow_id,channel_order_status,instance_id)','Channel order status must be unique in the list')
    ]