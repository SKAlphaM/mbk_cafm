# -*- coding: utf-8 -*-

from odoo import models, fields, api


class FMTicketType(models.Model):
    _name = 'mbk_fm.ticket_type'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'Ticket Types'

    name = fields.Char(string='Ticket Type Name', required=True, tracking=True)
    code = fields.Char(string='Ticket Type Code', required=True, tracking=True)
    team_id = fields.Many2one('mbk_fm.team', string='Maintenance Team', tracking=True, required=True)
    technician_id = fields.Many2one('res.users', string='Responsible', tracking=True)
    color = fields.Integer("Color Index", default=0)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, tracking=True)
    description = fields.Text(string='Description')
    is_approval_required = fields.Boolean(string='Approval Required', tracking=True)
    timeframe = fields.Float(string='Standard Timeframe', tracking=True, required=True, help="Standard Timeframe to resolve the case in days")
    active = fields.Boolean(string="Active", default=True, tracking=True)
    maintenance_ids = fields.One2many('mbk_fm.ticket', 'category_id', copy=False)
    maintenance_count = fields.Integer(string="Maintenance Count", compute='_compute_maintenance_count')

    def _compute_maintenance_count(self):
        maintenance_data = self.env['mbk_fm.ticket'].read_group([('ticket_type_id', 'in', self.ids)], ['ticket_type_id'], ['ticket_type_id'])
        mapped_data = dict([(m['ticket_type_id'][0], m['ticket_type_id_count']) for m in maintenance_data])
        for category in self:
            category.maintenance_count = mapped_data.get(category.id, 0)

    def action_view_tickets(self):
        return {
            'name': 'Maintenance Requests',
            'res_model': 'mbk_fm.ticket',
            'view_mode': 'list,form',
            'context': {'default_ticket_type_id': self.id},
            'domain': [('ticket_type_id', '=', self.id)],
            'target': 'current',
            'type': 'ir.actions.act_window',
        }








