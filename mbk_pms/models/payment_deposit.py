# -*- coding: utf-8 -*-

import ast
from datetime import date, datetime, timedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class PMSPaymentDeposit(models.Model):
    _name = 'mbk_pms.payment_deposit'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'Payment Deposit'

    name = fields.Char(string='Deposit No', tracking=True, default='Draft', copy=False)
    deposit_date = fields.Date(string='Deposit Date', default=fields.Date.context_today, copy=False)
    as_on_date = fields.Date(string='As On Date', default=fields.Date.context_today, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, copy=False, tracking=True, default='draft',
        help="""* When the deposit is created the status is \'Draft\'
                    \n* If the deposit is under confirmed, the status is \'Active\'.
                    \n* When user cancel deposit the status is \'cancelled\'.""")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    net_amount = fields.Monetary(string="Total Amount", readonly=True, compute='_compute_net_amount',
                                 store=True, default=0)
    note = fields.Text('Notes')
    owner_user_id = fields.Many2one('res.users', string='Created by User', default=lambda s: s.env.uid, copy=False)
    tenant_id = fields.Many2one('res.partner', string='Tenant')
    unit_id = fields.Many2one('mbk_pms.unit', string='Unit Location', tracking=True)
    property_id = fields.Many2one('mbk_pms.property', string='Property', tracking=True)
    state_id = fields.Many2one('res.country.state', string='Emirate', domain="[('country_id', '=', 2)]", tracking=True)
    depositing_bank_id = fields.Many2one('account.journal', string='Depositing Bank', domain="[('type', '=', 'bank')]", tracking=True, required=True)
    active = fields.Boolean(string="Active", default=True, tracking=True)
    deposit_line_ids = fields.One2many('mbk_pms.payment_deposit.line', 'deposit_id', string='Deposit Lines',
                                       required=True,
                                       states={'cancel': [('readonly', True)], 'active': [('readonly', True)]},
                                       copy=True, auto_join=True)
    payment_ref_id = fields.Integer(string='Reference ID')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id,
                                  store=True)

    @api.depends('deposit_line_ids')
    def _compute_net_rent(self):
        for deposit in self:
            net_amount = 0.00

            for line in deposit.deposit_line_ids:
                net_amount += line.amount

            deposit.update({
                'net_amount': net_amount,
            })

    @api.onchange('deposit_date')
    def onchange_contract_id(self):
        self.as_on_date = self.as_on_date

    @api.model
    def create(self, vals):
        # context: no_log, because subtype already handle this
        request = super(PMSPaymentDeposit, self).create(vals)
        return request

    def action_cancel(self):
        if self.filtered(lambda ticket: ticket.state == 'done'):
            raise UserError(_("Cannot cancel a deposit that is active."))
        else:
            self.write({'state': 'cancel'})

    def action_confirm(self):
        if self.deposit_line_ids:
            self.write({'state': 'active'})
            deposit_no = self.env['ir.sequence'].next_by_code('mbk_pms.payment_deposit')
            self.name = deposit_no
            for line in self.deposit_line_ids:
                if line.payment_line_id:
                    if line.payment_line_id.state == 'received':
                        line.payment_line_id.state = 'deposited'
                        line.payment_line_id.last_activity_date = date.today()
                        line.payment_line_id.deposited_date = date.today()
                        if self.depositing_bank_id != line.payment_line_id.depositing_bank_id:
                            line.payment_line_id.depositing_bank_id = self.depositing_bank_id
                        if line.payment_line_id.service_id.category == 'deposit':
                            deposit = self.env['mbk_pms.contract.deposit.line'].search([('contract_id', '=', line.payment_line_id.contract_id.id), ('deposit_id', '=', line.payment_line_id.service_id.id)])
                            if deposit and deposit.state == 'received':
                                deposit.state = 'deposited'
                    else:
                        raise UserError("Invalid cheque status found! %s %s" % (line.payment_line_id.name, line.payment_line_id.state))
        else:
            raise UserError(_("deposit details is missing"))

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_load_deposit(self):
        if self.state in ('draft'):
            if self.deposit_line_ids:
                self.deposit_line_ids.unlink()
            chq_filter = [('state', '=', 'received'), ('payment_mode', '=', 'chq'), ('ref_date', '<=', self.as_on_date)]
            if self.state_id:
                chq_filter.append(('state_id', '=', self.state_id.id))
            if self.property_id:
                chq_filter.append(('property_id', '=', self.property_id.id))
            if self.tenant_id:
                chq_filter.append(('tenant_id', '=', self.tenant_id.id))

            cheque_details = self.env['mbk_pms.contract.payment.line'].search(chq_filter, order='ref_date,contract_id')
            for line in cheque_details:
                self.env['mbk_pms.payment_deposit.line'].create(
                    {'deposit_id': self.id, 'payment_line_id': line.id, 'name': line.name + ' deposited', })
        else:
            raise UserError("Can't process active deposit voucher")


class PMSPaymentDepositLines(models.Model):
    _name = 'mbk_pms.payment_deposit.line'
    _description = 'Payment Deposit Lines'

    deposit_id = fields.Many2one('mbk_pms.payment_deposit', string='Deposit Reference', required=True,
                                 ondelete='cascade', index=True, copy=False)
    name = fields.Char(string='Description', required=True)
    payment_line_id = fields.Many2one('mbk_pms.contract.payment.line', string='Payment Reference',
                                      domain="[('state', '=', 'received'), ('payment_mode', '=', 'chq'), ('ref_date', '<=', parent.as_on_date)]")
    service_id = fields.Many2one(related='payment_line_id.service_id', string='Service')
    payment_mode = fields.Selection(related='payment_line_id.payment_mode', string='Payment Mode')
    ref_date = fields.Date(related='payment_line_id.ref_date', string='Date')
    ref_no = fields.Char(related='payment_line_id.ref_no', string='Cheque No')
    bank_id = fields.Many2one(related='payment_line_id.bank_id', string='Bank')
    amount = fields.Float(related='payment_line_id.amount', string="Amount")
    state = fields.Selection(related='payment_line_id.state', string='Status')
    contract_id = fields.Many2one(related='payment_line_id.contract_id', string='Contract No')
    tenant_id = fields.Many2one(related='payment_line_id.tenant_id', string='Tenant')
    unit_id = fields.Many2one(related='payment_line_id.unit_id', string='Unit No')
    property_id = fields.Many2one(related='payment_line_id.property_id', string='Property')

    @api.onchange('payment_line_id')
    def onchange_product_id(self):
        if self.payment_line_id:
            self.payment_mode = self.payment_line_id.payment_mode
            self.ref_no = self.payment_line_id.ref_no
            self.bank_id = self.payment_line_id.bank_id
            self.amount = self.payment_line_id.amount
            self.name = self.payment_line_id.note
