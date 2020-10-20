from odoo import models, fields, api


class res_partner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _commercial_fields(self):
        result = super(res_partner, self)._commercial_fields()
        if 'last_time_entries_checked' in result:
            result.remove('last_time_entries_checked')
        return result

    # @api.model
    # def create(self, vals):

    # 	rec = super(res_partner, self).create(vals)
    # 	account_receivable = self.env['account.account'].search([], limit=1)
    # 	account_payable = self.env['account.account'].search([], limit=1)
    # 	if not rec.property_account_receivable_id:
    # 		rec.property_account_receivable_id = account_receivable.id
    # 	if not rec.property_account_payable_id:
    # 		rec.property_account_payable_id = account_payable.id

    # 	return rec
