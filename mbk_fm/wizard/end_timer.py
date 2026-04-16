# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError


class FMEndTimerWizard(models.TransientModel):
    _name = 'mbk_fm.end_timer_wizard'
    _description = 'End Work order timer'

    ticket_id = fields.Many2one('mbk_fm.ticket', string='Maintenance Request')
    technician_id = fields.Many2one('res.users', string='Responsible')
    member_ids = fields.Many2many('hr.employee', string="Technicians", domain="[('department_id.name', '=', 'Maintenance')]")
    comment = fields.Text(string='Comment')

    @api.onchange('ticket_id')
    def onchange_equipment_id(self):
        if self.ticket_id.technician_id:
            self.technician_id = self.ticket_id.technician_id
        if self.ticket_id.member_ids:
            self.member_ids = self.ticket_id.member_ids
        if self.ticket_id.comment:
            self.comment = self.ticket_id.comment

    def action_end_timer(self):
        main_rec = self.env['mbk_fm.ticket'].browse(self.ticket_id.id)

        if main_rec.is_in_progress:
            main_rec.end_time = datetime.now()
            h = main_rec.end_time - main_rec.start_time
            main_rec.duration_hour = h.total_seconds() / 3600
            main_rec.is_in_progress = False
            main_rec.comment = self.comment
            main_rec.message_post(subject="Activity Update", body=self.comment)
            print(self.technician_id.name, self.member_ids.ids)
            self.env['mbk_fm.ticket.activity.line'].create({'name': self.comment, 'technician_id': main_rec.technician_id.id, 'member_ids': main_rec.member_ids.ids, 'start_time': main_rec.start_time,
                                                            'end_time': main_rec.end_time, 'duration_hour': main_rec.duration_hour})
        else:
            raise UserError("Timer is not active")
        return

    def action_done(self):
        self.action_end_timer()
        main_rec = self.env['mbk_fm.ticket'].browse(self.ticket_id.id)
        main_rec.action_done()
        return
