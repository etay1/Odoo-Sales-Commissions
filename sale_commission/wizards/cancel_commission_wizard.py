from odoo import api, fields, models


class CancelCommissionWizard(models.TransientModel):
    _name = 'cancel.commission.wizard'
    _description = 'Cancel Commission Wizard'

    commission_ids = fields.Many2many(
        'sale.commission',
        string='Settlements',
    )

    def cancel_commission(self):
        self.ensure_one()
        for commission in self.commission_ids:
            commission.state = 'cancel'

        return {'type': 'ir.actions.act_window_close'}
