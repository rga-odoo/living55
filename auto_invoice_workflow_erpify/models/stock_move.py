from odoo import models,fields,api


class stock_move(models.Model):
    _inherit = "stock.move"
    
    producturl = fields.Text("Product URL")
    
    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id):
        res= super(stock_move,self)._create_account_move_line(credit_account_id, debit_account_id, journal_id)
        for move in self.account_move_ids:
            if not move.global_channel_id:
                move.global_channel_id=self.picking_id.global_channel_id and self.picking_id.global_channel_id.id or False
                
        return res
    
    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        res = super(stock_move,self)._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
        for row in res:
            row[2].update({'global_channel_id':self.picking_id.global_channel_id and self.picking_id.global_channel_id.id or False})        
        return res

    def action_post(self):
        for invoice_line in self.invoice_line_ids:
            invoice_line.global_channel_id = self.global_channel_id.id or False