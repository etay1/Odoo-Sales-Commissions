from odoo import api, fields, models
from odoo import Command
from odoo.exceptions import ValidationError
from datetime import date


class ProcessCommissionWizard(models.TransientModel):
    _name = 'process.commission.wizard'
    _description = 'Process Commission Wizard'

    commission_ids = fields.Many2many(
        'sale.commission',
        string='Settlements',
    )

    @api.onchange('commission_ids')
    def _onchange_commission_ids(self):
        '''This function checks if all settlements are open.'''
        for record in self:
            if record.commission_ids and record.commission_ids.filtered(
                lambda r: r.state != 'open'
            ):
                raise ValidationError('Only open settlements can be processed.')

    def _create_vendor_bill(self, partner_id, commissions):
        '''Create a vendor bill for a partner if their commission state is set to open.'''
        self.ensure_one()

        # Helper function to create invoice lines for commissions.
        def create_invoice_line(commission):
            return {
                'name': f'Commission Payout ({commission.name})',
                'price_unit': commission.commission_amount,
            }

        # Generate invoice lines for each commission using the create_invoice_line function.
        invoice_lines = [
            (0, 0, create_invoice_line(commission)) for commission in commissions
        ]

        record = {
            'partner_id': partner_id.id,
            'move_type': 'in_invoice',
            'invoice_date': date.today(),
            'invoice_line_ids': invoice_lines,
        }

        return self.env['account.move'].create(record).id

    def process_commission(self):
        self.ensure_one()

        # Calculate commissions for each partner.
        commissions_record = {}
        for commission in self.commission_ids:
            partner_id = commission.partner_id
            if commissions_record.get(partner_id):
                commissions_record[partner_id].append(commission)
            else:
                commissions_record[partner_id] = [commission]

        for partner_id, commissions in commissions_record.items():
            vendor_bill_id = self._create_vendor_bill(partner_id, commissions)
            for commission in commissions:
                commission.write(
                    {
                        'vendor_bill_id': vendor_bill_id,
                        'state': 'bill',
                    }
                )

        return {'type': 'ir.actions.act_window_close'}
