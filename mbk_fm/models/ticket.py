# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class FMTicket(models.Model):
    _name = 'mbk_fm.ticket'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'FM Request'

    name = fields.Char(string='Maintenance Request No', tracking=True, default='New', copy=False)
    request_summary = fields.Char(string='Maintenance Request', required=True, tracking=True)
    request_date = fields.Date(string='Request Date', default=fields.Date.context_today, copy=False)
    ticket_date = fields.Datetime(string='Ticket Date', default=fields.Datetime.now, copy=False)
    ticket_type_id = fields.Many2one('mbk_fm.ticket_type', string='Ticket Type', required=True, tracking=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('assigned', 'Assigned'),
        ('in-progress', 'In Progress'),
        ('hold', 'Hold'),
        ('confirm', 'To Approve'),
        ('refuse', 'Rejected'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, copy=False, tracking=True, default='active',
        help="""* When the maintenance Request is created the status is \'Active\'
                    \n* If the maintenance Request is under verification, the status is \'To Approve\'.
                    \n* If the maintenance Request is completed then status is set to \'Done\'.
                    \n* When user cancel maintenance Request the status is \'cancelled\'.""")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, copy=False)
    description = fields.Text('Description')
    owner_user_id = fields.Many2one('res.users', string='Created by User', default=lambda s: s.env.uid, copy=False)
    category_id = fields.Many2one('mbk_fm.equipment_category', string='Equipment Category', tracking=True)
    equipment_id = fields.Many2one('mbk_fm.equipment', string='Equipment', ondelete='restrict', index=True)
    team_id = fields.Many2one('mbk_fm.team', string='Maintenance Team', tracking=True, required=True)
    allowed_member_ids = fields.Many2many('res.users', 'mbk_fm_ticket_allowed_users_rel', string="Allowed Assistants",
                                          domain="[('company_ids', 'in', company_id)]")
    technician_id = fields.Many2one('res.users', string='Responsible', tracking=True, copy=False)
    member_ids = fields.Many2many('hr.employee', 'mbk_fm_ticket_emp_rel', string="Technicians",
                                  domain="[('department_id.name', '=', 'Maintenance')]", copy=False)
    priority = fields.Selection([('0', 'Ver Low'), ('1', 'Low'), ('2', 'Normal'), ('3', 'High')], string='Priority',
                                copy=False, default=0)
    color = fields.Integer('Color Index', copy=False)
    close_date = fields.Date('Close Date', help="Date the maintenance was finished.", copy=False)
    maintenance_type = fields.Selection([('corrective', 'Corrective'), ('preventive', 'Preventive')],
                                        string='Maintenance Mode', default="corrective")
    schedule_date = fields.Datetime('Scheduled Date', tracking=True, copy=False,
                                    help="Date the maintenance team plans the maintenance.  It should not differ much from the Request Date. ")
    due_date = fields.Datetime('Due Date', help="Standard timeframe to resolve the task", copy=False)
    duration = fields.Float(help="Duration in hours.", copy=False)
    is_approval_required = fields.Boolean(string='Approval Required', default=1)
    done = fields.Boolean(string='Completed', default=0, copy=False)
    unit_id = fields.Many2one('mbk_pms.unit', string='Unit Location', tracking=True, required=True, copy=False)
    sub_location = fields.Char(string='Location of repair ', copy=False)
    property_id = fields.Many2one(related='unit_id.property_id', string='Property')
    state_id = fields.Many2one(related='property_id.state_id', string='Emirate')
    room_id = fields.Many2one(related='unit_id.rn_id', string='Room')
    customer_id = fields.Many2one('res.partner', string='Tenant')
    mobile = fields.Char(string='Mobile No')
    email = fields.Char(string='Email')
    registered_by = fields.Char(string='Complaint Reg By', copy=False)
    mode_of_contact = fields.Selection([('email', 'By Email'), ('phone', 'By Phone'), ('visit', 'By Visit'), ('other', 'Others')],
                                       string='Mode of Contact', required=True)
    active = fields.Boolean(string="Active", default=True, tracking=True, copy=False)
    start_time = fields.Datetime(string="Start Time", copy=False)
    end_time = fields.Datetime(string="End Time", copy=False)
    comment = fields.Text(string='Comment', copy=False)
    note = fields.Char(string='Notes', copy=False)
    duration_hour = fields.Float(string="Hours", help="Duration in hours.", default=0, copy=False)
    is_in_progress = fields.Boolean(string="In Progress", help="Work is going on", default=False, copy=False)
    activity_line_ids = fields.One2many('mbk_fm.ticket.activity.line', 'ticket_id', string='Activity Lines',
                                        states={'cancel': [('readonly', True)],
                                                'done': [('readonly', True)]}, copy=False, auto_join=True)
    material_request_ids = fields.One2many('mbk_fm.material_request', 'ticket_id', copy=False,
                                           domain="[('state', 'in', ('active','done')]")
    material_request_count = fields.Integer(compute='_compute_material_request_count', string="Material Request Count",
                                            store=True, copy=False)
    before_image = fields.Image(string="Before Image", attachment=True)
    after_image = fields.Image(string="After Image", attachment=True)
    live_duration = fields.Float('Real Duration', compute='_compute_duration', store=True)
    material_request_line_ids = fields.One2many('mbk_fm.material_request.line', 'ticket_id',
                                                string='Material Request Lines', copy=False)

    # For Information
    todo_request_ids = fields.One2many('mbk_fm.ticket', string="Open Requests", copy=False,
                                       compute='_compute_pending_ticket_count')
    todo_request_count = fields.Integer(string="Number of Requests", compute='_compute_pending_ticket_count')
    tenant_signature = fields.Binary(string="Tenant Signature") 
    tenant_contact_no = fields.Char(string="Tenant Contact No")
    supervisor_signature = fields.Binary(string="Supervisor Sign")

    def _compute_duration(self):
        self

    @api.onchange('equipment_id')
    def onchange_equipment_id(self):
        if self.equipment_id:
            if not self.technician_id:
                self.technician_id = self.equipment_id.technician_id if self.equipment_id.technician_id else self.equipment_id.category_id.technician_id
            self.category_id = self.equipment_id.category_id
            if self.equipment_id.team_id:
                self.team_id = self.equipment_id.team_id.id

    @api.onchange('category_id')
    def onchange_category_id(self):
        if not self.technician_id:
            self.technician_id = self.category_id.technician_id

    @api.onchange('owner_user_id')
    def onchange_owner_user_id(self):
        user_id = self.env['mbk_fm.user'].search([('user_id', '=', self.owner_user_id.id)])
        if user_id and user_id.is_based_on_user:
            self.technician_id = user_id.user_id
            self.team_id = user_id.team_id
            if user_id.ticket_type_id:
                self.ticket_type_id = user_id.ticket_type_id

    @api.onchange('team_id')
    def onchange_team_id(self):
        if self.team_id:
            self.allowed_member_ids = self.team_id.member_ids

    @api.onchange('ticket_type_id')
    def onchange_ticket_type_id(self):
        if not self.technician_id:
            self.technician_id = self.ticket_type_id.technician_id
            # self.team_id = self.ticket_type_id.team_id.id
        self.is_approval_required = self.ticket_type_id.is_approval_required

        if self.ticket_type_id.timeframe:
            self.due_date = self.ticket_date + timedelta(days=self.ticket_type_id.timeframe)
        else:
            self.due_date = self.ticket_date + timedelta(days=5)

    @api.onchange('unit_id')
    def onchange_unit_id(self):
        if self.unit_id:
            is_contact = self.env['ir.config_parameter'].get_param('mbk_fm_load_contact')
            if self.unit_id.customer_id:
                self.customer_id = self.unit_id.customer_id
                if is_contact:
                    if self.unit_id.description:
                        self.mobile = self.unit_id.description
                else:
                    if self.customer_id.mobile:
                        self.mobile = self.customer_id.mobile
                if self.customer_id.email:
                    self.email = self.customer_id.email
            else:
                self.customer_id = False
                self.mobile = False
                self.email = False
        else:
            self.customer_id = False
            self.mobile = False
            self.email = False

    @api.depends('unit_id', 'ticket_type_id')
    def _compute_pending_ticket_count(self):
        for rec in self:
            if rec.unit_id:
                is_contact = self.env['ir.config_parameter'].get_param('mbk_fm_load_contact')
                if is_contact and rec.unit_id.is_unit and rec.unit_id.use_type and rec.unit_id.use_type == 'res':
                    rec.todo_request_ids = self.env['mbk_fm.ticket'].search([('room_id', '=', rec.room_id.id), ('done', '=', False)])
                    if rec.ticket_type_id:
                        rec.todo_request_ids = rec.todo_request_ids.filtered(lambda r: r.ticket_type_id == rec.ticket_type_id)
                    rec.todo_request_count = len(rec.todo_request_ids)
                else:
                    rec.todo_request_ids = rec.unit_id.maintenance_ids.filtered(lambda r: not r.done)
                    if rec.ticket_type_id:
                        rec.todo_request_ids = rec.todo_request_ids.filtered(lambda r: r.ticket_type_id == rec.ticket_type_id)
                    rec.todo_request_count = len(rec.todo_request_ids)
            else:
                rec.todo_request_ids = []
                rec.todo_request_count = 0

    @api.depends('material_request_ids.state')
    def _compute_material_request_count(self):
        for ticket in self:
            ticket.material_request_count = len(ticket.material_request_ids)

    @api.model
    def create(self, vals):
        # context: no_log, because subtype already handle this
        vals['name'] = self.env['ir.sequence'].next_by_code('mbk_fm.ticket')
        request = super(FMTicket, self).create(vals)
        if request.owner_user_id or request.technician_id:
            request._add_followers()
        if request.equipment_id and not request.team_id:
            request.technician_id = request.equipment_id.technician_id
        request.activity_update()
        return request

    def write(self, vals):
        # Overridden to reset the kanban_state to normal whenever
        # the stage (stage_id) of the Maintenance Request changes.
        res = super(FMTicket, self).write(vals)
        if vals.get('owner_user_id') or vals.get('technician_id'):
            self._add_followers()
        if 'state' in vals and vals['state'] in ['done', 'confirm']:
            self.activity_feedback(['mbk_fm.mail_act_fm_maintenance_request'], feedback=self.comment)
        if vals.get('technician_id') or vals.get('schedule_date'):
            self.activity_update()
            if self.state in ['refuse', 'cancel', 'done', 'hold']:
                self.write({'state': 'assigned'})
        if vals.get('equipment_id'):
            # need to change description of activity also so unlink old and create new activity
            self.activity_unlink(['mbk_fm.mail_act_fm_maintenance_request'])
            self.activity_update()
        return res

    def activity_update(self):
        """ Update maintenance activities based on current record set state.
        It reschedule, unlink or create maintenance request activities. """
        self.filtered(lambda request: not request.schedule_date).activity_unlink(
            ['mbk_fm.mail_act_fm_maintenance_request'])
        for request in self.filtered(lambda request: request.schedule_date):
            date_dl = fields.Datetime.from_string(request.schedule_date).date()
            updated = request.activity_reschedule(
                ['mbk_fm.mail_act_fm_maintenance_request'],
                date_deadline=date_dl,
                new_user_id=request.technician_id.id or request.owner_user_id.id or self.env.uid)
            if not updated:
                if request.equipment_id:
                    note = _('Request planned for <a href="#" data-oe-model="%s" data-oe-id="%s">%s</a>') % (
                        request.equipment_id.name, request.equipment_id.id, request.equipment_id.display_name)
                else:
                    note = False
                request.activity_schedule(
                    'mbk_fm.mail_act_fm_maintenance_request',
                    fields.Datetime.from_string(request.schedule_date).date(),
                    note=note, user_id=request.technician_id.id or request.owner_user_id.id or self.env.uid)
            if request.state in ('active'):
                self.write({'state': 'assigned'})

    def _add_followers(self):
        for request in self:
            partner_ids = (request.owner_user_id.partner_id + request.technician_id.partner_id).ids
            request.message_subscribe(partner_ids=partner_ids)

    def action_cancel(self):
        if self.filtered(lambda ticket: ticket.state == 'done'):
            raise UserError(_("Cannot cancel a Maintenance request that is done."))
        if self.is_in_progress:
            raise UserError(_("Please stop the ongoing timer before cancel the ticket."))
        else:
            self.activity_unlink(['mbk_fm.mail_act_fm_maintenance_request'])
            self.write({'state': 'cancel'})
            self.done = True

    def action_hold(self):
        if self.filtered(lambda ticket: ticket.state == 'done'):
            raise UserError(_("Cannot cancel a Maintenance request that is done."))
        else:
            self.write({'state': 'hold'})

    def action_done(self):
        if self.filtered(lambda ticket: ticket.is_approval_required == 1):
            self.write({'state': 'confirm'})
            self.activity_schedule(
                'mbk_fm.mail_act_fm_ticket_approval',
                fields.Datetime.now().date(),
                note="To Approve for Maintenance Request no " + self.name,
                user_id=self.team_id.team_lead_id.id or self.owner_user_id.id or self.env.uid)
        else:
            self.write({'state': 'done'})
            self.close_date = date.today()
            self.done = True

    def action_confirm(self, comment):
        if self.filtered(lambda ticket: ticket.state == 'confirm'):
            self.write({'state': 'done'})
            self.close_date = date.today()
            self.done = True
            self.activity_feedback(['mbk_fm.mail_act_fm_ticket_approval'], feedback=comment)

    def action_reject(self, comment):
        if self.filtered(lambda ticket: ticket.state == 'confirm'):
            self.write({'state': 'refuse'})
            self.activity_unlink(['mbk_fm.mail_act_fm_ticket_approval'])

    def action_start_timer(self):
        if self.state == 'assigned':
            self.write({'state': 'in-progress'})
        if not self.is_in_progress:
            self.start_time = datetime.now()
            self.end_time = False
            self.is_in_progress = True
        else:
            raise UserError(_("Please close the on going timer"))

    def action_stop(self):
        if self.filtered(lambda ticket: ticket.state in ['in-progress']):
            if self.is_in_progress:
                self.end_time = datetime.now()
                h = self.end_time - self.start_time
                self.duration_hour = h.total_seconds() / 3600
                self.is_in_progress = False
            else:
                raise UserError(_("Timer is not active"))

    def action_view_pending_tickets(self):
        return {
            'name': 'Pending Ticket for ' + self.unit_id.name,
            'res_model': 'mbk_fm.ticket',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.todo_request_ids.ids)],
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_view_material_requests(self):
        return {
            'name': _('Material Requests'),
            'res_model': 'mbk_fm.material_request',
            'view_mode': 'list,form',
            'context': {'default_ticket_id': self.id},
            'domain': [('ticket_id', '=', self.id)],
            'target': 'current',
            'type': 'ir.actions.act_window',
        }

    def action_create_material_requests(self):
        return {
            'name': _('Material Requests'),
            'res_model': 'mbk_fm.material_request',
            'view_mode': 'form',
            'context': {'default_ticket_id': self.id},
            'target': 'current',
            'type': 'ir.actions.act_window',
        }

    def action_start_timer_wizard(self):
        return {
            'name': _('Start Timer'),
            'res_model': 'mbk_fm.start_timer_wizard',
            'view_mode': 'form',
            'context': {'default_ticket_id': self.id},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_end_timer_wizard(self):
        return {
            'name': _('End Timer'),
            'res_model': 'mbk_fm.end_timer_wizard',
            'view_mode': 'form',
            'context': {'default_ticket_id': self.id},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_done_update_state_wizard(self):
        return {
            'name': _('Update Status'),
            'res_model': 'mbk_fm.update_state_wizard',
            'view_mode': 'form',
            'context': {'default_ticket_id': self.id, 'default_status': 'done', 'default_label_name': 'Completed'},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_hold_update_state_wizard(self):
        return {
            'name': _('Update Status'),
            'res_model': 'mbk_fm.update_state_wizard',
            'view_mode': 'form',
            'context': {'default_ticket_id': self.id, 'default_status': 'hold', 'default_label_name': 'Hold'},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_confirm_update_state_wizard(self):
        return {
            'name': _('Update Status'),
            'res_model': 'mbk_fm.update_state_wizard',
            'view_mode': 'form',
            'context': {'default_ticket_id': self.id, 'default_status': 'confirm', 'default_label_name': 'Approve'},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_reject_update_state_wizard(self):
        return {
            'name': _('Update Status'),
            'res_model': 'mbk_fm.update_state_wizard',
            'view_mode': 'form',
            'context': {'default_ticket_id': self.id, 'default_status': 'refuse', 'default_label_name': 'Reject'},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_cancel_update_state_wizard(self):
        return {
            'name': _('Update Status'),
            'res_model': 'mbk_fm.update_state_wizard',
            'view_mode': 'form',
            'context': {'default_ticket_id': self.id, 'default_status': 'cancel', 'default_label_name': 'Cancel'},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }


class FMTicketActivityLines(models.Model):
    _name = 'mbk_fm.ticket.activity.line'
    _description = 'Ticket Activities'

    ticket_id = fields.Many2one('mbk_fm.ticket', string='Ticket Reference', required=True, ondelete='cascade',
                                index=True,
                                copy=False)
    name = fields.Text(string='Comment', required=True)
    technician_id = fields.Many2one('res.users', string='Responsible')
    member_ids = fields.Many2many('hr.employee', 'mbk_fm_ticket_line_emp_rel', string="Technicians",
                                  domain="[('department_id.name', '=', 'Maintenance')]")
    start_time = fields.Datetime(string="Start Time")
    end_time = fields.Datetime(string="End Time")
    duration_hour = fields.Float(string="Hours", help="Duration in hours.", default=0)
    unit_id = fields.Many2one(related='ticket_id.unit_id', string='Unit')
