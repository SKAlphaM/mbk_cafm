# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class PMSProperties(models.Model):
    _inherit = 'mbk_pms.property'

    maintenance_ids = fields.One2many('mbk_fm.ticket', 'property_id')
    maintenance_count = fields.Integer(compute='_compute_maintenance_count', string="Maintenance Count", store=True)

    @api.depends('maintenance_ids.state')
    def _compute_maintenance_count(self):
        for p in self:
            p.maintenance_count = len(p.maintenance_ids)

    def action_view_tickets(self):
        return {
            'name': _('Tickets'),
            'res_model': 'mbk_fm.ticket',
            'view_mode': 'list,form',
            'context': {'default_property_id': self.id},
            'domain': [('property_id', '=', self.id)],
            'target': 'current',
            'type': 'ir.actions.act_window',
        }


class PMSUnits(models.Model):
    _inherit = 'mbk_pms.unit'

    maintenance_ids = fields.One2many('mbk_fm.ticket', 'unit_id')
    maintenance_count = fields.Integer(compute='_compute_maintenance_count', string="Maintenance Count", store=True)

    @api.depends('maintenance_ids.state')
    def _compute_maintenance_count(self):
        for p in self:
            p.maintenance_count = len(p.maintenance_ids)

    def action_view_tickets(self):
        return {
            'name': _('Tickets'),
            'res_model': 'mbk_fm.ticket',
            'view_mode': 'list,form',
            'context': {'default_property_id': self.id},
            'domain': [('property_id', '=', self.id)],
            'target': 'current',
            'type': 'ir.actions.act_window',
        }

