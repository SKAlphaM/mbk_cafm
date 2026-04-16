# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError


class FMStartTimerWizard(models.TransientModel):
    _name = 'mbk_fm.start_timer_wizard'
    _description = 'Start Work order timer'

    ticket_id = fields.Many2one('mbk_fm.ticket', string='Maintenance Request')
    technician_id = fields.Many2one('res.users', string='Responsible')
    member_ids = fields.Many2many('hr.employee', string="Technicians", domain="[('department_id.name', '=', 'Maintenance')]")
    comment = fields.Text(string='Comment')

    @api.onchange('ticket_id')
    def onchange_ticket_id(self):
        if self.ticket_id.technician_id:
            self.technician_id = self.ticket_id.technician_id
        if self.ticket_id.member_ids:
            self.member_ids = self.ticket_id.member_ids

    def action_start_timer(self):
        main_rec = self.env['mbk_fm.ticket'].browse(self.ticket_id.id)

        if not self.member_ids:
            raise UserError("Please input the technician name")

        for member_id in self.member_ids:
            live_ticket = self.env['mbk_fm.ticket'].search([('is_in_progress', '=', True), ('member_ids', 'in', member_id.id)])
            if live_ticket:
                raise UserError("%s already working on ticket %s. Please close the ongoing timer" % (member_id.name, live_ticket[0].name))

        if not main_rec.is_in_progress:
            main_rec.write({'state': 'in-progress'})
            main_rec.start_time = datetime.now()
            main_rec.end_time = False
            main_rec.duration_hour = 0.00
            main_rec.member_ids = self.member_ids
            main_rec.is_in_progress = True
            main_rec.comment = self.comment
            # main_rec.message_post(body=self.comment)
        else:
            raise UserError("Please close the on going timer")
        return










