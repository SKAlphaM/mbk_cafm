# -*- coding: utf-8 -*-

import ast
from datetime import date, datetime, timedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError


class PMSBreakRequest(models.Model):
    _name = 'mbk_pms.break_request'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'Lease Breaking Request'

    name = fields.Char(string='Breaking Request No', tracking=True, default='Draft', copy=False)
    request_date = fields.Date(string='Request Date', default=fields.Date.context_today, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, copy=False, tracking=True, default='draft',
        help="""* When the breaking request is created the status is \'Draft\'
                    \n* If the breaking request is under confirmed, the status is \'Active\'.
                    \n* When user cancel breaking request the status is \'cancelled\'.""")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id,
                                  store=True)
    contract_id = fields.Many2one('mbk_pms.contract', string='Contract No', required=True, tracking=True, domain="[('state', '=', 'open'), ('renewed_contract_id', '=', False), ('breaking_contract_id', '=', False)]")
    break_contract_id = fields.Many2one('mbk_pms.break_contract', string='Break Contract No', readonly=True, tracking=True)
    tenant_id = fields.Many2one(related='contract_id.partner_id', string='Tenant')
    contract_amount = fields.Monetary(related='contract_id.net_rent_amount', string="Contract Amount")
    start_date = fields.Date(related='contract_id.start_date', string='Start Date', help="Contract Valid from date.")
    expiry_date = fields.Date(related='contract_id.expiry_date', string='Expiration Date', help="Contract Valid upto.")
    breaking_date = fields.Date(string='Breaking Date', copy=False, required=True, tracking=True)
    no_of_days = fields.Integer(string='No Of Days', copy=False)
    remaining_days = fields.Integer(string='Remaining Days', copy=False)
    units = fields.Char(related='contract_id.units', string='Units')
    property_id = fields.Many2one(related='contract_id.property_id', string='Property')
    note = fields.Text('Notes')
    owner_user_id = fields.Many2one('res.users', string='Created by User', default=lambda s: s.env.uid, copy=False)
    active = fields.Boolean(string="Active", default=True, tracking=True)

    @api.onchange('breaking_date')
    def onchange_breaking_date(self):
        if self.breaking_date:
            if not self.start_date <= self.breaking_date <= self.expiry_date:
                self.update({'breaking_date': False,
                             'remaining_days': False,
                             'no_of_days': False,
                             })
                raise UserError("Enter Valid breaking date.")
            if self.expiry_date and self.breaking_date:
                self.remaining_days = (self.expiry_date - self.breaking_date).days + 1
            if self.start_date and self.breaking_date:
                self.no_of_days = (self.breaking_date - self.start_date).days + 1

    @api.model
    def create(self, vals):
        # context: no_log, because subtype already handle this
        request = super(PMSBreakRequest, self).create(vals)
        return request

    def action_cancel(self):
        if self.filtered(lambda breaking_request: breaking_request.state == 'done'):
            raise UserError(_("Cannot cancel a breaking request that is active."))
        else:
            self.write({'state': 'cancel'})

    def action_confirm(self):
        if self.expiry_date >= self.breaking_date >= self.start_date:
            self.write({'state': 'active'})
            request_no = self.env['ir.sequence'].next_by_code('mbk_pms.break_request')
            self.name = request_no

            contract_units = self.env['mbk_pms.contract.unit.line'].search([('contract_id', '=', self.contract_id.id)])

            for line in contract_units:
                line.unit_id.available_from_date = self.breaking_date + timedelta(days=1)

            self.contract_id.breaking_request_id = self.id

        else:
            raise UserError(_("breaking request date is not valid"))

    def action_draft(self):
        self.write({'state': 'draft'})
        contract_units = self.env['mbk_pms.contract.unit.line'].search([('contract_id', '=', self.contract_id.id)])
        for line in contract_units:
            line.unit_id.available_from_date = False

