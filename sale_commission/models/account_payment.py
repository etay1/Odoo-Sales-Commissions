from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    commission_ids = fields.One2many('sale.commission', 'payment_id')
    commission_count = fields.Integer(compute='_compute_commission_count')

    @api.depends('commission_ids')
    def _compute_commission_count(self):
        for record in self:
            record.commission_count = len(record.commission_ids)

    def action_view_commissions(self):
        self.ensure_one()
        return {
            'name': 'Sales Commissions',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'sale.commission',
            'domain': [('payment_id', '=', self.id)],
        }

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        self.commission_ids.write({'state': 'open'})
        self.commission_ids._compute_state()
        return res

    def action_draft(self):
        res = super(AccountPayment, self).action_draft()
        if self.commission_ids.filtered(lambda r: r.state == 'paid'):
            raise UserError(
                'You cannot reset to draft a payment that has paid commissions.'
            )
        self.commission_ids.write({'state': 'cancel'})
        return res

    def action_cancel(self):
        res = super(AccountPayment, self).action_cancel()
        self.commission_ids.write({'state': 'cancel'})
        return res
