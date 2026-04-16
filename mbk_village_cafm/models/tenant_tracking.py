from odoo import models, fields, api


class TenantTracking(models.Model):
    _name = 'mbk_village.tenant.tracking'
    _description = 'Tenant Tracking'
    _order = 'date desc'

    tenant_id = fields.Many2one(
        'mbk_village.tenant',
        string='Tenant',
        required=True,
        ondelete='cascade'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    action = fields.Selection([
        ('on_boarding', 'On Boarding'),
        ('off_boarding', 'Off Boarding'),
        ('gate', 'Gate'),
        ('mess_hall', 'Mess Hall'),
        ('laundry', 'Laundry')
    ], string='Access Status', required=True)

    date = fields.Datetime(string='Date', default=fields.Datetime.now)

    notes = fields.Text(string='Notes')


