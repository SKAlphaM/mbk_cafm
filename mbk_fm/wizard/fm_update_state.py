# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError


class FMUpdateStatusWizard(models.TransientModel):
    _name = 'mbk_fm.status_wizard'
    _description = 'Update status with comment'

    doc_id = fields.Integer(string='Document ID')
    status = fields.Text(string='Status')
    label_name = fields.Text(string='Label Name')
    comment = fields.Text(string='Comment', required='True')
    model_name = fields.Text(string='Model')

    def action_update_state(self):
        if self.model_name == 'mr':
            main_rec = self.env['mbk_fm.material_request'].browse(self.doc_id)
            partner_ids = (main_rec.owner_user_id.partner_id).ids
        else:
            raise UserError("Invalid Model Name")

        if self.status == 'hold':
            main_rec.action_hold()
            main_rec.message_post(subject=self.label_name, body=self.comment)
        elif self.status == 'cancel':
            main_rec.action_cancel()
            main_rec.message_post(subject=self.label_name, body=self.comment)
        elif self.status == 'refuse':
            main_rec.action_reject()
            main_rec.message_post(subject=self.label_name, body=self.comment, message_type='comment',  sub_type_id='1', partner_ids=partner_ids)
        elif self.status == 'confirm':
            main_rec.action_confirm(self.comment)
            main_rec.message_post(subject=self.label_name, body="Material Request Approved", message_type='comment',  sub_type_id='1', partner_ids=partner_ids)
        elif self.status == 'done':
            main_rec.action_done(self.comment)
        else:
            raise UserError("Invalid Status")
        return










