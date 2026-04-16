# -*- coding: utf-8 -*-

from odoo import models, fields, api


class FMEquipmentCategory(models.Model):
    _name = 'mbk_fm.equipment_category'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'FM Equipment Category'

    name = fields.Char(string='Category Name', required=True, tracking=True)
    code = fields.Char(string='Category Code', required=True, tracking=True)
    team_id = fields.Many2one('mbk_fm.team', string='Maintenance Team', tracking=True, required=True)
    technician_id = fields.Many2one('res.users', string='Responsible', tracking=True)
    color = fields.Integer("Color Index", default=0)
    note = fields.Text('Comments')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, tracking=True)
    active = fields.Boolean(string="Active", default=True, tracking=True)
    equipment_ids = fields.One2many('mbk_fm.equipment', 'category_id', string='Equipments', copy=False)
    equipment_count = fields.Integer(string="Equipment", compute='_compute_equipment_count')
    maintenance_ids = fields.One2many('mbk_fm.ticket', 'category_id', copy=False)
    maintenance_count = fields.Integer(string="Maintenance Count", compute='_compute_maintenance_count')

    def _compute_equipment_count(self):
        equipment_data = self.env['mbk_fm.equipment'].read_group([('category_id', 'in', self.ids)], ['category_id'], ['category_id'])
        mapped_data = dict([(m['category_id'][0], m['category_id_count']) for m in equipment_data])
        for category in self:
            category.equipment_count = mapped_data.get(category.id, 0)

    def _compute_maintenance_count(self):
        maintenance_data = self.env['mbk_fm.ticket'].read_group([('category_id', 'in', self.ids)], ['category_id'], ['category_id'])
        mapped_data = dict([(m['category_id'][0], m['category_id_count']) for m in maintenance_data])
        for category in self:
            category.maintenance_count = mapped_data.get(category.id, 0)

    def action_view_equipments(self):
        return {
            'name': 'Equipments',
            'res_model': 'mbk_fm.equipment',
            'view_mode': 'kanban,tree,form',
            'context': {'default_category_id': self.id},
            'domain': [('category_id', '=', self.id)],
            'target': 'current',
            'type': 'ir.actions.act_window',
        }

    def action_view_tickets(self):
        return {
            'name': 'Maintenance Requests',
            'res_model': 'mbk_fm.ticket',
            'view_mode': 'list,form',
            'context': {'default_category_id': self.id},
            'domain': [('category_id', '=', self.id)],
            'target': 'current',
            'type': 'ir.actions.act_window',
        }








