# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class FMUser(models.Model):
    _name = 'mbk_fm.user'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'FM User Preference'

    name = fields.Char(string='User Name', required=True, tracking=True)
    user_id = fields.Many2one('res.users', string='User', tracking=True, required=True)
    active = fields.Boolean(string="Active", default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    team_id = fields.Many2one('mbk_fm.team', string='Team', tracking=True, required=True)
    team_lead_id = fields.Many2one('res.users', string='Team Lead', tracking=True, required=True)
    ticket_type_id = fields.Many2one('mbk_fm.ticket_type', string='Ticket Type', tracking=True)
    is_based_on_user = fields.Boolean(string="User Default", default=True, tracking=True)
    description = fields.Text(string='Description')

    @api.onchange('user_id')
    def onchange_user_id(self):
        if self.user_id:
            self.name = self.user_id.name
            team_id = self.env['mbk_fm.team'].search([('member_ids', 'in', self.user_id.id)])
            if team_id:
                if len(team_id) == 1:
                    for team in team_id:
                        self.team_id = team.id
                        self.team_lead_id = team.team_lead_id.id










