from odoo import api, fields, models
from odoo.exceptions import UserError


SALE_COMMISSION_VIEW = {
    'name': 'Sales Commissions',
    'type': 'ir.actions.act_window',
    'view_mode': 'tree,form',
    'res_model': 'sale.commission',
}


class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_commission_ids = fields.One2many('sale.commission', 'account_move_id')
    bill_commission_ids = fields.One2many('sale.commission', 'vendor_bill_id')

    account_move_count = fields.Integer(compute='_compute_account_move_count')

    @api.depends('invoice_commission_ids', 'bill_commission_ids')
    def _compute_account_move_count(self):
        '''This function is used to count the number of commissions associated with this account move'''
        for record in self:
            record.account_move_count = (
                len(record.bill_commission_ids)
                if record.move_type == 'in_invoice'
                else len(record.invoice_commission_ids)
            )

    @api.depends('move_type')
    def action_view_commissions(self):
        '''This function returns an action that display existing commissions associated with this account move via smart button'''
        self.ensure_one()
        if self.move_type == 'in_invoice':
            return SALE_COMMISSION_VIEW | {'domain': [('vendor_bill_id', '=', self.id)]}
        else:
            return SALE_COMMISSION_VIEW | {'domain': [('account_move_id', '=', self.id)]}

    def button_draft(self):
        '''This function is used to set the state of the commission to cancel when the invoice is set to draft'''
        res = super(AccountMove, self).button_draft()
        for record in self:
            if record.invoice_commission_ids.filtered(lambda r: r.state == 'paid'):
                raise UserError(
                    'You cannot reset to draft an invoice with paid commissions.'
                )
            record.invoice_commission_ids.write(
                {'state': 'cancel'}
            ) if record.move_type == 'out_invoice' else record.bill_commission_ids.write(
                {'state': 'bill'}
            )
            return res

    def button_cancel(self):
        '''This function is used to set the state of the commission to cancel when the invoice is set to cancel'''
        res = super(AccountMove, self).button_cancel()
        for record in self:
            record.invoice_commission_ids.write({'state': 'cancel'})
            record.bill_commission_ids.write({'state': 'cancel'})
        return res
