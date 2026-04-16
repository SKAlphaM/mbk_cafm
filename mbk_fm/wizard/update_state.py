# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError


class FMStartTimerWizard(models.TransientModel):
    _name = 'mbk_fm.update_state_wizard'
    _description = 'FM Update status with comment'

    ticket_id = fields.Many2one('mbk_fm.ticket', string='Maintenance Request')
    status = fields.Text(string='Status')
    label_name = fields.Text(string='Label Name')
    comment = fields.Text(string='Comment', required='True')

    def action_update_state(self):
        main_rec = self.env['mbk_fm.ticket'].browse(self.ticket_id.id)

        if self.status == 'hold':
            main_rec.action_hold()
            main_rec.message_post(subject=self.label_name, body=self.comment)
        elif self.status == 'cancel':
            main_rec.action_cancel()
            main_rec.message_post(subject=self.label_name, body=self.comment)
        elif self.status == 'refuse':
            if main_rec.team_id.team_lead_id.id == self.env.uid or self.env.user.has_group('mbk_fm.group_fm_manager'):
                main_rec.action_reject(self.comment)
                main_rec.message_post(subject=self.label_name, body=self.comment)
            else:
                raise UserError("Invalid User")
        elif self.status == 'confirm':
            if main_rec.team_id.team_lead_id.id == self.env.uid or self.env.user.has_group('mbk_fm.group_fm_manager'):
                main_rec.action_confirm(self.comment)
                # main_rec.message_post(subject=self.label_name+'d', body=self.comment)
            else:
                raise UserError("Invalid User")
        elif self.status == 'done':
            main_rec.action_done()
            # main_rec.message_post(subject=self.label_name, body=self.comment)
        else:
            raise UserError("Invalid Status")

        return










