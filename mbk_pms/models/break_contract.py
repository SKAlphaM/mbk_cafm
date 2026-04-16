# -*- coding: utf-8 -*-

import ast
from datetime import date, datetime, timedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError


class PMSBreakContract(models.Model):
    _name = 'mbk_pms.break_contract'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'Break Contract'

    name = fields.Char(string='Breaking No', tracking=True, default='Draft', copy=False)
    break_date = fields.Date(string='Date', default=fields.Date.context_today, copy=False)
    breaking_request_id = fields.Many2one('mbk_pms.break_request', string='Breaking Request', copy=False, required=True, domain="[('state', '=', 'active'), ('break_contract_id', '=', False)]")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'To Approve'),
        ('refuse', 'Rejected'),
        ('active', 'Active'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, copy=False, tracking=True, default='draft',
        help="""* When the breaking contract is created the status is \'Draft\'
                    \n* If the breaking contract is under confirmed, the status is \'Active\'.
                    \n* When user cancel breaking contract the status is \'cancelled\'.""")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id,
                                  store=True)
    contract_id = fields.Many2one('mbk_pms.contract', string='Contract No', required=True, tracking=True,
                                  domain="[('state', '=', 'open')]")
    tenant_id = fields.Many2one(related='contract_id.partner_id', string='Tenant')
    contract_amount = fields.Monetary(related='contract_id.net_rent_amount', string="Contract Amount")
    start_date = fields.Date(related='contract_id.start_date', string='Start Date', help="Contract Valid from date.")
    expiry_date = fields.Date(related='contract_id.expiry_date', string='Expiration Date', help="Contract Valid upto.")
    breaking_date = fields.Date(string='Breaking Date', copy=False, required=True, tracking=True)
    no_of_days = fields.Integer(string='No Of Days', copy=False, store=True, readonly=True)
    remaining_days = fields.Integer(string='Remaining Days', copy=False, store=True, readonly=True)
    total_days = fields.Integer(string='Total Days', copy=False, store=True, readonly=True)
    units = fields.Char(related='contract_id.units', string='Units')
    property_id = fields.Many2one(related='contract_id.property_id', string='Property')
    security_deposit = fields.Monetary(related='contract_id.total_deposit', string="Security Deposit")
    penalty_days = fields.Integer(string="Penalty Days", default=0, copy=False)
    rent_received = fields.Monetary(string="Rent Received from Tenant", copy=False, store=True, readonly=True, compute='_compute_rent_received')
    balance_security_deposit = fields.Monetary(string="Refundable Security Deposit", copy=False, store=True, readonly=True, compute='_compute_refundable_sd')
    total_received = fields.Monetary(string="Total Received", copy=False, store=True, readonly=True)
    total_deductions = fields.Monetary(string="Total Due From Tenant", copy=False, store=True, readonly=True, compute='_compute_deduction_amount')
    net_due_amount = fields.Monetary(string="Net Amount Due To Tenant", copy=False, store=True, readonly=True)
    note = fields.Text('Notes')
    owner_user_id = fields.Many2one('res.users', string='Created by User', default=lambda s: s.env.uid, copy=False)
    active = fields.Boolean(string="Active", default=True, tracking=True)
    deduction_line_ids = fields.One2many('mbk_pms.break_contract.line', 'break_contract_id', string='Deduction Lines',
                                         states={'cancel': [('readonly', True)], 'close': [('readonly', True)]}, copy=False, auto_join=True)

    @api.onchange('breaking_date')
    def onchange_breaking_date(self):
        if self.breaking_date:
            if not self.start_date <= self.breaking_date <= self.expiry_date:
                self.breaking_date = False
                raise UserError(_("Enter Valid breaking date."))

        if self.expiry_date and self.breaking_date:
            self.remaining_days = (self.expiry_date - self.breaking_date).days + 1
            for line in self.deduction_line_ids:
                if line.deduction_id.code == 'a':
                    name = line.deduction_id.name+'(' + str(self.no_of_days) + ' Days)'
                    if self.total_days:
                        amount = (self.no_of_days * self.contract_amount)/self.total_days
                    else:
                        amount = 0.0
                    line.name = name
                    line.amount = amount
        if self.start_date and self.breaking_date:
            self.no_of_days = (self.breaking_date - self.start_date).days + 1
        if self.start_date and self.expiry_date:
            self.total_days = (self.expiry_date - self.start_date).days + 1

    @api.onchange('penalty_days')
    def onchange_penalty_days(self):
        if self.total_days and self.penalty_days:
            for line in self.deduction_line_ids:
                if line.deduction_id.code == 'c':
                    name = line.deduction_id.name+'(' + str(self.penalty_days) + ' Days)'
                    if self.total_days:
                        amount = (self.penalty_days * self.contract_amount)/self.total_days
                    else:
                        amount = 0.00
                    line.name = name
                    line.amount = amount

    @api.onchange('breaking_request_id')
    def onchange_breaking_request_id(self):
        if self.breaking_request_id:
            self.tenant_id = self.breaking_request_id.tenant_id
            self.contract_id = self.breaking_request_id.contract_id
            self.breaking_date = self.breaking_request_id.breaking_date
            self.note = self.breaking_request_id.note

    @api.onchange('rent_received', 'balance_security_deposit')
    def onchange_received_amount(self):
        if self.rent_received and self.balance_security_deposit:
            self.total_received = self.rent_received + self.balance_security_deposit
        else:
            self.total_received = 0.00

    @api.depends('deduction_line_ids.amount')
    def _compute_deduction_amount(self):
        amount = 0.00
        for line in self.deduction_line_ids:
            amount += line.amount
        self.update({
            'total_deductions': amount,
        })

    @api.onchange('total_received', 'total_deductions')
    def onchange_net_due_amount(self):
        self.net_due_amount = self.total_received - self.total_deductions

    @api.depends('contract_id.payment_line_ids')
    def _compute_rent_received(self):
        rent_received = 0.00
        for bc in self:
            for line in bc.contract_id.payment_line_ids:
                if line and line.state == 'cleared' and line.service_id.category == 'rent':
                    rent_received += line.amount
            bc.update({
                'rent_received': rent_received,
            })

    @api.depends('contract_id.deposit_line_ids')
    def _compute_refundable_sd(self):
        balance_security_deposit = 0.00
        for bc in self:
            for line in bc.contract_id.deposit_line_ids:
                if line and line.state == 'cleared':
                    balance_security_deposit += line.amount
            bc.update({
                'balance_security_deposit': balance_security_deposit,
            })

    @api.model
    def create(self, vals):
        # context: no_log, because subtype already handle this
        contract = super(PMSBreakContract, self).create(vals)
        self.breaking_request_id.break_contract_id = self.id
        return contract

    def action_cancel(self):
        if self.filtered(lambda breaking_contract: breaking_contract.state == 'active'):
            raise UserError(_("Cannot cancel a terminated contract"))
        else:
            self.write({'state': 'cancel'})

    def action_confirm(self, comment):
        if self.filtered(lambda offer: offer.state == 'confirm'):
            self.activity_feedback(['mbk_pms.mail_act_pms_break_contract_approval'], feedback=comment)
            if self.expiry_date >= self.breaking_date >= self.start_date:
                self.write({'state': 'active'})
                break_no = self.env['ir.sequence'].next_by_code('mbk_pms.break_contract')
                self.name = break_no
                contract_units = self.env['mbk_pms.contract.unit.line'].search([('contract_id', '=', self.contract_id.id)])
                today = date.today()
                for line in contract_units:
                    if self.breaking_date <= today:
                        line.unit_id.available_from_date = False
                        line.unit_id.state = 'available'
                        line.unit_id.status = 'vacant'
                        if line.unit_id.contract_id and line.unit_id.contract_id.id == self.contract_id.id:
                            line.unit_id.contract_id = False
                            line.unit_id.customer_id = False
                    else:
                        line.unit_id.available_from_date = self.breaking_date + timedelta(days=1)
                        line.unit_id.state = 'available'

                self.contract_id.breaking_contract_id = self.id
                if self.breaking_request_id:
                    self.contract_id.breaking_request_id.state = 'done'
                    self.breaking_request_id.break_contract_id = self.id

            else:
                raise UserError(_("breaking contract date is not valid"))
        else:
            raise UserError("Invalid Status")

    def action_reject(self, comment):
        if self.filtered(lambda offer: offer.state == 'confirm'):
            self.write({'state': 'refuse'})
            self.activity_unlink(['mbk_pms.mail_act_pms_break_contract_approval'])

    def action_draft(self):
        if self.filtered(lambda breaking_contract: breaking_contract.state in ('active', 'done')):
            raise UserError(_("Cannot draft a terminated contract"))
        else:
            self.write({'state': 'draft'})

    def action_load_deductions(self):
        if self.state in ('draft'):
            if self.deduction_line_ids:
                self.deduction_line_ids.unlink()
            deductions = self.env['mbk_pms.service'].search([('category', '=', 'ded'), ('active', '=', True)])
            for line in deductions:
                name = line.name
                amount = 0.00
                if line.code == 'a':
                    name += '(' + str(self.no_of_days) + ' Days)'
                    if self.total_days and self.no_of_days:
                        amount = (self.no_of_days * self.contract_amount)/self.total_days
                if line.code == 'c':
                    name += '(' + str(self.penalty_days) + ' Days)'
                    if self.total_days and self.penalty_days:
                        amount = (self.penalty_days * self.contract_amount)/self.total_days
                self.env['mbk_pms.break_contract.line'].create({'break_contract_id': self.id, 'deduction_id': line.id, 'name': name, 'amount': amount, })
        else:
            raise UserError("Can't process active entry")

    def action_done_update_state_wizard(self):
        return {
            'name': 'Update Status',
            'res_model': 'mbk_pms.update_state_wizard',
            'view_mode': 'form',
            'context': {'default_doc_id': self.id, 'default_status': 'done',
                        'default_label_name': 'Submit for Approval', 'default_model_name': 'break_contract'},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_confirm_update_state_wizard(self):
        return {
            'name': 'Update Status',
            'res_model': 'mbk_pms.update_state_wizard',
            'view_mode': 'form',
            'context': {'default_doc_id': self.id, 'default_status': 'confirm', 'default_label_name': 'Approve',
                        'default_model_name': 'break_contract'},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_cancel_update_state_wizard(self):
        return {
            'name': 'Update Status',
            'res_model': 'mbk_pms.update_state_wizard',
            'view_mode': 'form',
            'context': {'default_doc_id': self.id, 'default_status': 'cancel', 'default_label_name': 'Cancel',
                        'default_model_name': 'break_contract'},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_reject_update_state_wizard(self):
        return {
            'name': 'Update Status',
            'res_model': 'mbk_pms.update_state_wizard',
            'view_mode': 'form',
            'context': {'default_doc_id': self.id, 'default_status': 'refuse', 'default_label_name': 'Reject',
                        'default_model_name': 'break_contract'},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_done(self, comment):
        approval_user_id = self.env['ir.config_parameter'].get_param('mbk_pms_lease_offer_approver_id')
        if self.filtered(lambda break_contract: break_contract.state == 'draft'):
            self.write({'state': 'confirm'})
            self.activity_schedule(
                'mbk_pms.mail_act_pms_break_contract_approval',
                fields.Datetime.now().date(),
                note="To Approve Break Contract for " + self.contract_id.name + ' ' + self.tenant_id.name + '\n' + comment,
                user_id=approval_user_id or self.owner_user_id.id or self.env.uid)

    @api.model
    def _cron_update_break_unit_status(self):
        """
            update unit status based on break contract date
        """
        today = date.today()
        for break_contract in self.search([('state', '=', 'active'), ('breaking_date', '<', today)]):
            contract_units = self.env['mbk_pms.contract.unit.line'].search([('contract_id', '=', break_contract.contract_id.id)])
            for line in contract_units:
                if break_contract.contract_id.id == line.contract_id.id:
                    line.unit_id.available_from_date = False
                    line.unit_id.status = 'vacant'
                    line.unit_id.contract_id = False
                    line.unit_id.customer_id = False
            break_contract.state = 'done'


class PMSBreakContractLines(models.Model):
    _name = 'mbk_pms.break_contract.line'
    _description = 'Break Lease Contract Computation'

    break_contract_id = fields.Many2one('mbk_pms.break_contract', string='Break Contract Reference', required=True, ondelete='cascade', index=True, copy=False)
    deduction_id = fields.Many2one('mbk_pms.service', string='Deductions', required=True, domain="[('category', '=', 'ded')]")
    name = fields.Char(string='Description', required=True)
    amount = fields.Float(string="Amount", default=0)
    company_id = fields.Many2one(related='break_contract_id.company_id', string='Company')
    is_edit = fields.Boolean(string="Is Editable", default=True)

    @api.onchange('deduction_id')
    def onchange_deduction_id(self):
        if self.deduction_id and self.deduction_id.code in ('a', 'c'):
            self.is_edit = 0
        self.name = self.deduction_id.description



