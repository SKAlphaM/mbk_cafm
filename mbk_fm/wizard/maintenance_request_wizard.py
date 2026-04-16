# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class MaintenanceRequestWizard(models.TransientModel):
    _name = 'maintenance.request.wizard'
    _description = 'Maintenance Request Wizard'

    from_date = fields.Date(string='From Date', default='2022-09-01')
    to_date = fields.Date(string='To Date', default=fields.Date.context_today)
    case_type = fields.Many2one('mbk_fm.ticket_type', string='Case Type')
    team_id = fields.Many2one('mbk_fm.team', string='Team')
    unit_id = fields.Many2one('mbk_pms.unit', string='Unit')
    property_id = fields.Many2one('mbk_pms.property', string='Property')
    priority = fields.Selection([('0', 'Ver Low'), ('1', 'Low'), ('2', 'Normal'), ('3', 'High')], string='Priority')
    technician_id = fields.Many2one('res.users', string='Responsible')
    mode_of_contact = fields.Selection([('email', 'By Email'), ('phone', 'By Phone'), ('visit', 'By Visit')], string='Mode of Contact')
    state = fields.Selection([
        ('active', 'Active'),
        ('assigned', 'Assigned'),
        ('in-progress', 'In Progress'),
        ('hold', 'Hold'),
        ('todo', 'To Do'),
        ('confirm', 'To Approve'),
        ('refuse', 'Rejected'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),], string='Status', default='todo')
    optional_close_date = fields.Boolean('Completion Date ')
    optional_complaint_reg_by = fields.Boolean('Complaint Reg By')
    optional_details_of_complaint = fields.Boolean('Details Of Complaints')
    optional_customer = fields.Boolean('Customer')
    optional_techicians = fields.Boolean('Techicians')
    optional_mode_of_contact = fields.Boolean('Mode Of Contact')

    def action_create_report(self):
        data = {}
        data = self.pre_print_report(data)
        return self.env.ref(
            'mbk_fm.action_mbk_fm_maintenance_request_report').report_action(
            self, data=data)

    def pre_print_report(self, data):
        data['from_date'] = self.from_date
        data['to_date'] = self.to_date
        data['case_type'] = self.case_type.id
        data['team_id'] = self.team_id.id
        data['unit_id'] = self.unit_id.id
        data['property_id'] = self.property_id.id
        data['priority'] = self.priority
        data['technician_id'] = self.technician_id.id
        data['mode_of_contact'] = self.mode_of_contact
        data['state'] = self.state
        data['optional_close_date'] = self.optional_close_date
        data['optional_mode_of_contact'] = self.optional_mode_of_contact
        data['optional_complaint_reg_by'] = self.optional_complaint_reg_by
        data['optional_details_of_complaint'] = self.optional_details_of_complaint
        data['optional_customer'] = self.optional_customer
        data['optional_techicians'] = self.optional_techicians
        return data

    # @api.model
    # def _cron_maintenance_requests_email(self):
    #     """
    #         Generates maintenance request on the next_action_date or today if none exists
    #     """
    #     test = self.env['maintenance.request.wizard'].create({
    #         'from_date': '2022-09-01',
    #         'to_date': '2022-09-20',
    #         'state': 'active',
            
    #     })
    #     print('testtttttttttttttttttttttt', test)
    #     data = {}
    #     data['from_date'] = '2022-09-01'
    #     data['to_date'] = '2022-09-20'
    #     k = self.env.ref(
    #         'mbk_fm.action_mbk_fm_maintenance_request_report').report_action(
    #         self, data=data)
    #     template_id = self.env.ref('mbk_fm.maintenance_requests_email_template').id
    #     template = self.env['mail.template'].browse(template_id)
    #     template.send_mail(test.id, force_send=True)
        
