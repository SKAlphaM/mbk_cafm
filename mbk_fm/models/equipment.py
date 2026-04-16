# -*- coding: utf-8 -*-

from odoo import models, fields, api, SUPERUSER_ID, _
from datetime import date, datetime, timedelta


class FMTeam(models.Model):
    _name = 'mbk_fm.equipment'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'FM Equipment'

    name = fields.Char(string='Equipment Name', required=True, tracking=True)
    code = fields.Char(string='Equipment Code', required=True, tracking=True)
    category_id = fields.Many2one('mbk_fm.equipment_category', string='Equipment Category', tracking=True)
    ticket_type_id = fields.Many2one('mbk_fm.ticket_type', string='Ticket Type', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    custodian = fields.Char(string='Custodian', tracking=True)
    team_id = fields.Many2one('mbk_fm.team', string='Maintenance Team', tracking=True, required=True)
    technician_id = fields.Many2one('res.users', string='Responsible', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Vendor', tracking=True)
    partner_ref = fields.Char('Vendor Reference', tracking=True)
    unit_id = fields.Many2one('mbk_pms.unit', string='Unit Location', tracking=True, required=True)
    location = fields.Char('Location', tracking=True)
    subcontractor = fields.Char('Subcontractor', tracking=True)
    model = fields.Char('Model', tracking=True)
    serial_no = fields.Char('Serial Number', copy=False, tracking=True)
    assign_date = fields.Date('Assigned Date', tracking=True)
    effective_date = fields.Date('Effective Date', default=fields.Date.context_today, required=True,
                                 help="Date at which the equipment became effective. This date will be used to compute the Mean Time Between Failure.")
    cost = fields.Float('Cost')
    note = fields.Text('Note')
    warranty_date = fields.Date('Warranty Expiration Date')
    scrap_date = fields.Date('Scrap Date')
    period = fields.Integer('Days between each preventive maintenance')
    maintenance_duration = fields.Float(help="Maintenance Duration in hours.")
    color = fields.Integer("Color Index", default=0)
    active = fields.Boolean(string="Active", default=True, tracking=True)
    next_action_date = fields.Date(string='Date of the next preventive maintenance', default=fields.Date.context_today)
    maintenance_ids = fields.One2many('mbk_fm.ticket', 'equipment_id')
    maintenance_count = fields.Integer(compute='_compute_maintenance_count', string="Maintenance Count", store=True)
    maintenance_open_count = fields.Integer(string="Current Maintenance", default=0)

    _sql_constraints = [
        ('serial_no', 'unique(model, serial_no)', "Another asset already exists with this serial number!"),
    ]

    @api.depends('effective_date', 'period', 'maintenance_ids.request_date', 'maintenance_ids.close_date')
    def _compute_next_maintenance(self):
        date_now = fields.Date.context_today(self)
        equipments = self.filtered(lambda x: x.period > 0)
        for equipment in equipments:
            next_maintenance_todo = self.env['mbk_fm.ticket'].search([
                ('equipment_id', '=', equipment.id),
                ('maintenance_type', '=', 'preventive'),
                ('state', 'not in', ['done', 'cancel']),
                ('close_date', '=', False)], order="request_date asc", limit=1)
            last_maintenance_done = self.env['mbk_fm.ticket'].search([
                ('equipment_id', '=', equipment.id),
                ('maintenance_type', '=', 'preventive'),
                ('state', '=', 'done'),
                ('close_date', '!=', False)], order="close_date desc", limit=1)
            if next_maintenance_todo and last_maintenance_done:
                next_date = next_maintenance_todo.request_date
                date_gap = next_maintenance_todo.request_date - last_maintenance_done.close_date
                # If the gap between the last_maintenance_done and the next_maintenance_todo one is bigger than 2 times the period and next request is in the future
                # We use 2 times the period to avoid creation too closed request from a manually one created
                if date_gap > timedelta(0) and date_gap > timedelta(
                        days=equipment.period) * 2 and next_maintenance_todo.request_date > date_now:
                    # If the new date still in the past, we set it for today
                    if last_maintenance_done.close_date + timedelta(days=equipment.period) < date_now:
                        next_date = date_now
                    else:
                        next_date = last_maintenance_done.close_date + timedelta(days=equipment.period)
            elif next_maintenance_todo:
                next_date = next_maintenance_todo.request_date
                date_gap = next_maintenance_todo.request_date - date_now
                # If next maintenance to do is in the future, and in more than 2 times the period, we insert an new request
                # We use 2 times the period to avoid creation too closed request from a manually one created
                if date_gap > timedelta(0) and date_gap > timedelta(days=equipment.period) * 2:
                    next_date = date_now + timedelta(days=equipment.period)
            elif last_maintenance_done:
                next_date = last_maintenance_done.close_date + timedelta(days=equipment.period)
                # If when we add the period to the last maintenance done and we still in past, we plan it for today
                if next_date < date_now:
                    next_date = date_now
            else:
                next_date = equipment.effective_date + timedelta(days=equipment.period)
            equipment.next_action_date = next_date
        (self - equipments).next_action_date = False

    @api.depends('maintenance_ids.state')
    def _compute_maintenance_count(self):
        for equipment in self:
            equipment.maintenance_count = len(equipment.maintenance_ids)
            equipment.maintenance_open_count = len(
                equipment.maintenance_ids.filtered(lambda x: x.state not in ['done', 'cancel']))

    def _create_new_request(self, schedule_date):
        self.ensure_one()
        self.env['mbk_fm.ticket'].create({
            'name': 'New',
            'request_summary': _('Preventive Maintenance - %s', self.name),
            'request_date': schedule_date,
            'schedule_date': datetime.combine(schedule_date, datetime.min.time()),
            'category_id': self.category_id.id,
            'ticket_type_id': self.ticket_type_id.id,
            'unit_id': self.unit_id.id,
            'property_id': self.unit_id.property_id.id,
            'customer_id': self.unit_id.customer_id.id,
            'equipment_id': self.id,
            'note': self.subcontractor,
            'maintenance_type': 'preventive',
            'owner_user_id': self.technician_id.id,
            'technician_id': self.technician_id.id,
            'team_id': self.team_id.id,
            'duration': self.maintenance_duration,
            'company_id': self.company_id.id or self.env.company.id,
            'done': 0,
            'due_date': schedule_date + timedelta(days=self.ticket_type_id.timeframe),
            'mode_of_contact': 'other',
        })

    @api.model
    def _cron_generate_requests(self):
        """
            Generates maintenance request on the next_action_date or today if none exists
        """
        for equipment in self.search([('period', '>', 0)]):
            next_requests = self.env['mbk_fm.ticket'].search([('done', '=', False),
                                                              ('equipment_id', '=', equipment.id),
                                                              ('maintenance_type', '=', 'preventive'),
                                                              ('request_date', '=', equipment.next_action_date)])
            if not next_requests:
                equipment._create_new_request(equipment.next_action_date)

    def action_view_tickets(self):
        return {
            'name': 'Maintenance Requests',
            'res_model': 'mbk_fm.ticket',
            'view_mode': 'list,form',
            'context': {'default_equipment_id': self.id},
            'domain': [('equipment_id', '=', self.id)],
            'target': 'current',
            'type': 'ir.actions.act_window',
        }
