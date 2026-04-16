# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PmsPropertyUnit(models.Model):
    _name = 'mbk_pms.unit'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'Property Units'

    name = fields.Char(string='Unit Name', required=True, tracking=True)
    code = fields.Char(string='Unit Code', required=True, tracking=True)
    type_id = fields.Many2one('mbk_pms.unit_type', string='Unit Type', required=True, tracking=True)
    rn_id = fields.Many2one('mbk_pms.unit_no', string='Room No', required=True, tracking=True)
    property_id = fields.Many2one('mbk_pms.property', string='Property', required=True)
    status = fields.Selection([('occupied', 'Occupied'), ('vacant', 'Vacant'), ('booked', 'Booked'), ('non-renewal', 'Non Renewal'), ('inactive', 'Inactive'), ('maintenance', 'Maintenance')],
                              string='Status', tracking=True)
    sq_ft = fields.Float(string='Sq.ft')
    use_type = fields.Selection([('res', 'Residential'), ('com', 'Commercial')], string='Use Type', tracking=True)
    contract_id = fields.Many2one('mbk_pms.contract', string="Contract No", tracking=True)
    customer_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string="Active", default=True, tracking=True)
    is_unit = fields.Boolean(string="Unit", default=True, tracking=True)
    unit_ref_id = fields.Integer(string='Reference ID')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    contract_ids = fields.One2many('mbk_pms.contract', 'unit_id')
    contract_count = fields.Integer(compute='_compute_contract_count', string="Contract Count", store=True, default=0)
    state_id = fields.Many2one(related='property_id.state_id', string='Emirate', copy=False, store=True)
    state = fields.Selection([
        ('booked', 'Booked'),
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('unavailable', 'Unavailable'), ], string='State', index=True, readonly=True, copy=False, tracking=True, default='available',
        help="""* When the unit is booked for new contract is \'Booked\'
                        \n* If the unit is available for lease, the status is \'Available\'.
                        \n* If the unit is currently occupied \'Occupied\'.
                        \n* When user unit is not ready for leasing \'Unavailable\'.""")
    available_from_date = fields.Date('Available From', help="Unit Available for new contract.", copy=False)
    no_of_beds = fields.Integer(string="No of Beds", default=0)
    no_of_baths = fields.Integer(string="No of Baths", default=0)
    rent = fields.Float(string='Rent', tracking=True)

    @api.depends('contract_ids.state')
    def _compute_contract_count(self):
        for c in self:
            c.contract_count = len(c.contract_ids)

    @api.onchange('is_unit')
    def onchange_is_unit(self):
        if not self.is_unit:
            self.state = 'unavailable'

    def action_view_contracts(self):
        return {
            'name': 'Contracts',
            'res_model': 'mbk_pms.contract',
            'view_mode': 'list,form',
            'domain': [('unit_id', '=', self.id)],
            'target': 'current',
            'type': 'ir.actions.act_window',
        }




