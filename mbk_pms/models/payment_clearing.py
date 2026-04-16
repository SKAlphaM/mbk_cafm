# -*- coding: utf-8 -*-

import ast
from datetime import date, datetime, timedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class PMSPaymentClearing(models.Model):
    _name = 'mbk_pms.payment_clearing'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'Payment Clearing'

    name = fields.Char(string='Clearing No', tracking=True, default='Draft', copy=False)
    clearing_date = fields.Date(string='Clearing Date', default=fields.Date.context_today, copy=False)
    as_on_date = fields.Date(string='As On Date', default=fields.Date.context_today, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, copy=False, tracking=True, default='draft',
        help="""* When the clearing is created the status is \'Draft\'
                    \n* If the clearing is under confirmed, the status is \'Active\'.
                    \n* When user cancel clearing the status is \'cancelled\'.""")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    net_amount = fields.Monetary(string="Total Amount", readonly=True, compute='_compute_net_amount',
                                 store=True, default=0)
    note = fields.Text('Notes')
    owner_user_id = fields.Many2one('res.users', string='Created by User', default=lambda s: s.env.uid, copy=False)
    tenant_id = fields.Many2one('res.partner', string='Tenant')
    unit_id = fields.Many2one('mbk_pms.unit', string='Unit Location', tracking=True)
    property_id = fields.Many2one('mbk_pms.property', string='Property', tracking=True)
    state_id = fields.Many2one('res.country.state', string='Emirate', domain="[('country_id', '=', 2)]", tracking=True)
    journal_id = fields.Many2one('account.journal', string='Account', domain="[('type', 'in', ('bank', 'cash'))]", tracking=True, required=True)
    payment_mode = fields.Selection([('chq', 'Cheque'), ('cash', 'Cash'), ('transfer', 'Transfer')], string='Payment Mode', copy=False, default='chq')
    payment_state = fields.Selection([('deposited', 'Deposited'), ('received', 'Received')], string='Payment State')
    active = fields.Boolean(string="Active", default=True, tracking=True)
    clearing_line_ids = fields.One2many('mbk_pms.payment_clearing.line', 'clearing_id', string='Clearing Lines', required=True,
                                        states={'cancel': [('readonly', True)], 'active': [('readonly', True)]}, copy=True, auto_join=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id,
                                  store=True)

    @api.depends('clearing_line_ids')
    def _compute_net_rent(self):
        for clearing in self:
            net_amount = 0.00

            for line in clearing.clearing_line_ids:
                net_amount += line.amount

            clearing.update({
                'net_amount': net_amount,
            })

    @api.onchange('clearing_date')
    def onchange_contract_id(self):
        self.as_on_date = self.as_on_date

    @api.onchange('journal_id')
    def onchange_journal_id(self):
        if self.journal_id:
            if self.journal_id.type == 'bank':
                self.payment_mode = 'chq'
            if self.journal_id.type == 'cash':
                self.payment_mode = 'cash'

    @api.onchange('payment_mode')
    def onchange_payment_mode(self):
        if self.payment_mode:
            if self.payment_mode == 'chq':
                self.payment_state = 'deposited'
            else:
                self.payment_state = 'received'

    @api.model
    def create(self, vals):
        # context: no_log, because subtype already handle this
        request = super(PMSPaymentClearing, self).create(vals)
        return request

    def action_cancel(self):
        if self.filtered(lambda ticket: ticket.state == 'done'):
            raise UserError(_("Cannot cancel a clearing that is active."))
        else:
            self.write({'state': 'cancel'})

    def action_confirm(self):
        if self.clearing_line_ids:
            self.write({'state': 'active'})
            clearing_no = self.env['ir.sequence'].next_by_code('mbk_pms.payment_clearing')
            self.name = clearing_no
            for line in self.clearing_line_ids:
                if line.payment_line_id:
                    if line.payment_line_id.state == 'deposited':
                        line.payment_line_id.state = 'cleared'
                        line.payment_line_id.last_activity_date = date.today()
                        if line.payment_line_id.service_id.category == 'deposit':
                            deposit = self.env['mbk_pms.contract.deposit.line'].search(
                                [('contract_id', '=', line.payment_line_id.contract_id.id),
                                 ('deposit_id', '=', line.payment_line_id.service_id.id)])
                            if deposit and deposit.state:
                                deposit.state = 'cleared'
                    else:
                        raise UserError("Invalid cheque status found! %s %s" % (line.payment_line_id.name, line.payment_line_id.state))
        else:
            raise UserError(_("clearing details is missing"))

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_load_clearing(self):
        if self.state in ('draft'):
            self.clearing_line_ids.unlink()
            if self.journal_id and self.payment_mode and self.as_on_date and self.payment_state:
                if self.payment_state == 'received':
                    chq_filter = [('state', '=', self.payment_state), ('payment_mode', '=', self.payment_mode), ('received_date', '<=', self.as_on_date)]
                else:
                    chq_filter = [('state', '=', self.payment_state), ('payment_mode', '=', self.payment_mode), ('deposited_date', '<=', self.as_on_date)]

                if self.journal_id:
                    chq_filter.append(('depositing_bank_id', '=', self.journal_id.id))
                if self.state_id:
                    chq_filter.append(('state_id', '=', self.state_id.id))
                if self.property_id:
                    chq_filter.append(('property_id', '=', self.property_id.id))
                if self.tenant_id:
                    chq_filter.append(('tenant_id', '=', self.tenant_id.id))
                cheque_details = self.env['mbk_pms.contract.payment.line'].search(chq_filter, order='ref_date,contract_id')
                for line in cheque_details:
                    self.env['mbk_pms.payment_clearing.line'].create(
                        {'clearing_id': self.id, 'name': line.name + ' cleared', 'payment_line_id': line.id, })
        else:
            raise UserError("Can't process active clearing voucher")


class PMSPaymentClearingLines(models.Model):
    _name = 'mbk_pms.payment_clearing.line'
    _description = 'Payment clearing Lines'

    clearing_id = fields.Many2one('mbk_pms.payment_clearing', string='clearing Reference', required=True,
                                 ondelete='cascade', index=True, copy=False)
    name = fields.Char(string='Description', required=True)
    payment_line_id = fields.Many2one('mbk_pms.contract.payment.line', string='Payment Reference',
                                      domain="[('state', '=', parent.payment_state), ('payment_mode', '=', parent.payment_mode), ('ref_date', '<=', parent.as_on_date)]")
    payment_mode = fields.Selection(related='payment_line_id.payment_mode', string='Payment Mode')
    ref_date = fields.Date(related='payment_line_id.ref_date', string='Date')
    ref_no = fields.Char(related='payment_line_id.ref_no', string='Cheque No')
    bank_id = fields.Many2one(related='payment_line_id.bank_id', string='Bank')
    deposited_date = fields.Date(related='payment_line_id.deposited_date', string='Deposit Date')
    amount = fields.Float(related='payment_line_id.amount', string="Amount")
    state = fields.Selection(related='payment_line_id.state', string='Status')
    contract_id = fields.Many2one(related='payment_line_id.contract_id', string='Contract No')
    tenant_id = fields.Many2one(related='payment_line_id.tenant_id', string='Tenant No')
    unit_id = fields.Many2one(related='payment_line_id.unit_id', string='Unit No')
    property_id = fields.Many2one(related='payment_line_id.property_id', string='Property')
