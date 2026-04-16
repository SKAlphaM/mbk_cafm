# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta


class FMTeam(models.Model):
    _name = 'mbk_fm.team'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'FM Teams'
    _order = 'sequence,id'

    name = fields.Char(string='Team Name', required=True, tracking=True)
    code = fields.Char(string='Team Code', required=True, tracking=True)
    active = fields.Boolean(string="Active", default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    team_lead_id = fields.Many2one('res.users', string='Team Lead', tracking=True, required=True)
    store_user_id = fields.Many2one('res.users', string='Store in-charge', tracking=True, domain=lambda self: [
        ("id", "in", self.env.ref('stock.group_stock_user').users.ids)])
    member_ids = fields.Many2many('res.users', 'mbk_fm_team_users_rel', string="Team Members", domain="[('company_ids', 'in', company_id)]")
    description = fields.Text(string='Description')
    color = fields.Integer("Color Index", default=0)
    request_ids = fields.One2many('mbk_fm.ticket', 'team_id', copy=False)
    equipment_ids = fields.One2many('mbk_fm.equipment', 'team_id', copy=False)
    sequence = fields.Integer(string="Sequence ", default=10)

    # For the dashboard only
    todo_request_ids = fields.One2many('mbk_fm.ticket', string="Requests", copy=False, compute='_compute_todo_requests')
    todo_request_count = fields.Integer(string="Number of Requests", compute='_compute_todo_requests')
    todo_request_count_date = fields.Integer(string="Number of Requests Scheduled", compute='_compute_todo_requests')
    todo_request_count_high_priority = fields.Integer(string="Number of Requests in High Priority", compute='_compute_todo_requests')
    todo_request_count_block = fields.Integer(string="Number of Requests Blocked", compute='_compute_todo_requests')
    todo_request_count_unscheduled = fields.Integer(string="Number of Requests Unscheduled", compute='_compute_todo_requests')
    todo_request_count_overdue = fields.Integer(string="Number of Requests OverDue", compute='_compute_todo_requests')
    todo_request_count_confirm = fields.Integer(string="Number of Requests To Approve", compute='_compute_todo_requests')
    todo_request_count_timer = fields.Integer(string="Number of Requests with running timer", compute='_compute_todo_requests')
    todo_request_count_timer_due = fields.Integer(string="Number of Requests Timer more than 12 Hours", compute='_compute_todo_requests')
    todo_request_count_month_due = fields.Integer(string="Number of Requests due more than month", compute='_compute_todo_requests')

    @api.depends('request_ids.state')
    def _compute_todo_requests(self):
        for team in self:
            team.todo_request_ids = team.request_ids.filtered(lambda e: e.done == False)
            team.todo_request_count = len(team.todo_request_ids)
            team.todo_request_count_date = len(team.todo_request_ids.filtered(lambda e: e.schedule_date != False and e.state != 'confirm'))
            team.todo_request_count_high_priority = len(team.todo_request_ids.filtered(lambda e: e.priority == '3' and e.state != 'confirm'))
            team.todo_request_count_block = len(team.todo_request_ids.filtered(lambda e: e.state in ['refuse', 'hold']))
            team.todo_request_count_unscheduled = len(team.todo_request_ids.filtered(lambda e: not e.schedule_date and e.state != 'confirm'))
            team.todo_request_count_overdue = len(team.todo_request_ids.filtered(lambda e: e.due_date and e.due_date < datetime.now()))
            team.todo_request_count_confirm = len(team.todo_request_ids.filtered(lambda e: e.state == 'confirm'))
            team.todo_request_count_timer_due = len(team.todo_request_ids.filtered(lambda e: e.is_in_progress and datetime.now() > e.start_time + timedelta(hours=12)))
            team.todo_request_count_timer = len(team.todo_request_ids.filtered(lambda e: e.is_in_progress and datetime.now() <= e.start_time + timedelta(hours=12)))
            team.todo_request_count_month_due = len(team.todo_request_ids.filtered(lambda e: datetime.now() > e.ticket_date + +timedelta(days=30)))

    @api.depends('equipment_ids')
    def _compute_equipment(self):
        for team in self:
            team.equipment_count = len(team.equipment_ids)

    def action_timer_due_tickets(self):
        time_due_ids = self.todo_request_ids.filtered(lambda e: e.is_in_progress and datetime.now() > e.start_time + timedelta(hours=12))
        return {
            'name': 'Timer Due Maintenance Requests',
            'res_model': 'mbk_fm.ticket',
            'view_mode': 'list,form',
            'domain': [('id', 'in', time_due_ids.ids)],
            'target': 'current',
            'type': 'ir.actions.act_window',
        }

    def action_timer_tickets(self):
        timer_ids = self.todo_request_ids.filtered(lambda e: e.is_in_progress and datetime.now() <= e.start_time + timedelta(hours=12))
        return {
            'name': 'Timer Due Maintenance Requests',
            'res_model': 'mbk_fm.ticket',
            'view_mode': 'list,form',
            'domain': [('id', 'in', timer_ids.ids)],
            'target': 'current',
            'type': 'ir.actions.act_window',
        }

    def action_month_due_tickets(self):
        month_due_ids = self.todo_request_ids.filtered(lambda e: datetime.now() > e.ticket_date + timedelta(days=30))
        return {
            'name': 'Month Due Maintenance Requests',
            'res_model': 'mbk_fm.ticket',
            'view_mode': 'list,form',
            'domain': [('id', 'in', month_due_ids.ids)],
            'target': 'current',
            'type': 'ir.actions.act_window',
        }






