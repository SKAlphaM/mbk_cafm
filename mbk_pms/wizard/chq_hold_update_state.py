# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError


class PMSUpdateChqHoldStatus(models.TransientModel):
    _name = 'mbk_pms.chq_hold_update_state_wizard'
    _description = 'Update Cheque Hold Status with comment'

    cheque_hold_id = fields.Many2one('mbk_pms.cheque_hold', string='Cheque Hold ID')
    status = fields.Text(string='Status')
    label_name = fields.Text(string='Label Name')
    comment = fields.Text(string='Comment', required='True')

    def action_update_state(self):
        main_rec = self.env['mbk_pms.cheque_hold'].browse(self.cheque_hold_id.id)
        partner_ids = (main_rec.owner_user_id.partner_id).ids

        if self.status == 'hold':
            main_rec.action_hold()
            main_rec.message_post(subject=self.label_name, body=self.comment)
        elif self.status == 'cancel':
            main_rec.action_cancel()
            main_rec.message_post(subject=self.label_name, body=self.comment)
        elif self.status == 'refuse':
            main_rec.action_reject(self.comment)
            main_rec.message_post(subject=self.label_name, body=self.comment, message_type='comment',  sub_type_id='1', partner_ids=partner_ids)
        elif self.status == 'confirm':
            main_rec.action_confirm(self.comment)
            main_rec.message_post(subject=self.label_name, body="Contract Approved", message_type='comment',  sub_type_id='1', partner_ids=partner_ids)
        elif self.status == 'done':
            main_rec.action_done(self.comment)
        else:
            raise UserError("Invalid Status")
        return










