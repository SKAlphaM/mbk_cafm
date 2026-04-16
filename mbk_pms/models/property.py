# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PmsProperty(models.Model):
    _name = 'mbk_pms.property'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'Property master'

    name = fields.Char(string='Property Name', required=True, tracking=True)
    code = fields.Char(string='Property Code', required=True, tracking=True)
    property_type_id = fields.Many2one('mbk_pms.property_type', string='Property Type', required=True, tracking=True)
    status = fields.Selection([('active', 'Active'), ('inactive', 'Inactive'), ('maintenance', 'Maintenance')], string='Status', required=True, tracking=True)
    country_id = fields.Many2one('res.country', string='Country', required=True)
    state_id = fields.Many2one('res.country.state', string='Emirate', domain="[('country_id', '=', country_id)]", required=True, tracking=True)
    city = fields.Char(string='City')
    street = fields.Char(string='Street')
    address = fields.Text(string='Address')
    contact_no = fields.Char(string='Contact No')
    description = fields.Text(string='Description')
    property_ref_id = fields.Integer(string='Reference ID')
    active = fields.Boolean(string="Active", default=True, tracking=True)
    image = fields.Image(string="Image")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)

    unit_ids = fields.One2many('mbk_pms.unit', 'property_id', domain="[('is_unit', '=', True)]", copy=False)
    unit_count = fields.Integer(compute='_compute_unit_count', string="Unit Count", copy=False)
    unit_vacant = fields.Integer(compute='_compute_unit_count', string="Unit Vacant", copy=False)
    unit_occupied = fields.Integer(compute='_compute_unit_count', string="Unit Occupied", copy=False)
    unit_non_renewal = fields.Integer(compute='_compute_unit_count', string="Unit Non-Renewal", copy=False)
    unit_others = fields.Integer(compute='_compute_unit_count', string="Unit Others", copy=False)
    occupancy_percentage = fields.Float(compute='_compute_unit_count', string="Occupancy %", copy=False)

    @api.depends('address')
    def _auto_address(self):
        for record in self:
            if not record.address:
                record.address = '%s %s, %s, %s' % (record.street or '',  record.city or '', record.state_id.name, record.country_id.name)

    @api.onchange('street', 'city', 'state_id', 'country_id')
    def onchange_unit_id(self):
        if not self.address:
            self.address = '%s %s, %s, %s' % (self.street or '', self.city or '', self.state_id.name, self.country_id.name)

    @api.depends('unit_ids')
    def _compute_unit_count(self):
        for p in self:
            p.unit_count = len(p.unit_ids.filtered(lambda e: e.status != 'inactive' and e.is_unit))
            p.unit_vacant = len(p.unit_ids.filtered(lambda e: e.status == 'vacant' and e.is_unit))
            p.unit_occupied = len(p.unit_ids.filtered(lambda e: e.status == 'occupied' and e.is_unit))
            p.unit_non_renewal = len(p.unit_ids.filtered(lambda e: e.status == 'non-renewal' and e.is_unit))
            p.unit_others = len(p.unit_ids.filtered(lambda e: (e.status == 'maintenance' or e.status == 'booked') and e.is_unit))
            if p.unit_count and p.unit_count > 0:
                p.occupancy_percentage = ((p.unit_occupied + p.unit_non_renewal)*100 / p.unit_count)
            else:
                p.occupancy_percentage = 0

    def action_view_units(self):
        return {
            'name': _('Units'),
            'res_model': 'mbk_pms.unit',
            'view_mode': 'list,form',
            'context': {'default_property_id': self.id, 'search_default_filter_type_active': 1},
            'domain': [('property_id', '=', self.id)],
            'target': 'current',
            'type': 'ir.actions.act_window',
        }

    def action_view_units_occupied(self):
        return {
            'name': _('Units'),
            'res_model': 'mbk_pms.unit',
            'view_mode': 'list,form',
            'context': {'default_property_id': self.id, 'search_default_filter_type_active': 1},
            'domain': [('property_id', '=', self.id), ('status', '=', 'occupied')],
            'target': 'current',
            'type': 'ir.actions.act_window',
        }

    def action_view_units_vacant(self):
        return {
            'name': _('Units'),
            'res_model': 'mbk_pms.unit',
            'view_mode': 'list,form',
            'context': {'default_property_id': self.id, 'search_default_filter_type_active': 1},
            'domain': [('property_id', '=', self.id), ('status', '=', 'vacant')],
            'target': 'current',
            'type': 'ir.actions.act_window',
        }

    def action_view_units_non_renewal(self):
        return {
            'name': _('Units'),
            'res_model': 'mbk_pms.unit',
            'view_mode': 'list,form',
            'context': {'default_property_id': self.id},
            'domain': [('property_id', '=', self.id), ('status', '=', 'non-renewal')],
            'target': 'current',
            'type': 'ir.actions.act_window',
        }


