# -*- coding: utf-8 -*-

import ast
from datetime import date, datetime, timedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class PMSPaymentCollection(models.Model):
    _name = 'mbk_pms.payment_collection'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'Payment Collection'

    name = fields.Char(string='Receipt No', tracking=True, default='Draft', copy=False)
    receipt_date = fields.Date(string='Receipt Date', default=fields.Date.context_today, copy=False)
    contract_id = fields.Many2one('mbk_pms.contract', string='Contract No', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, copy=False, tracking=True, default='draft',
        help="""* When the receipt is created the status is \'Draft\'
                    \n* If the receipt is under confirmed, the status is \'Active\'.
                    \n* When user cancel receipt the status is \'cancelled\'.""")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    net_amount = fields.Monetary(string="Total Amount", readonly=True, compute='_compute_net_amount',
                                        store=True, default=0)
    note = fields.Text('Notes')
    owner_user_id = fields.Many2one('res.users', string='Created by User', default=lambda s: s.env.uid, copy=False)
    unit_id = fields.Many2one('mbk_pms.unit', string='Unit Location', tracking=True)
    property_id = fields.Many2one('mbk_pms.property', string='Property', tracking=True)
    tenant_id = fields.Many2one('res.partner', string='Tenant')
    active = fields.Boolean(string="Active", default=True, tracking=True)
    receipt_line_ids = fields.One2many('mbk_pms.payment_collection.line', 'receipt_id', string='Receipt Lines', required=True,
                                       states={'cancel': [('readonly', True)], 'active': [('readonly', True)]}, copy=True, auto_join=True)
    payment_ref_id = fields.Integer(string='Reference ID')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id, store=True)

    @api.model
    def create(self, vals):
        # context: no_log, because subtype already handle this
        request = super(PMSPaymentCollection, self).create(vals)
        return request

    def action_cancel(self):
        if self.filtered(lambda ticket: ticket.state == 'done'):
            raise UserError(_("Cannot cancel a receipt that is active."))
        else:
            self.write({'state': 'cancel'})

    def action_confirm(self):
        if self.receipt_line_ids:
            self.write({'state': 'active'})
            contract_no = self.env['ir.sequence'].next_by_code('mbk_pms.payment_collection')
            self.name = contract_no
            for line in self.receipt_line_ids:
                if not line.payment_line_id:
                    pm = line._fields['payment_mode'].selection
                    pm_dict = dict(pm)
                    payment_mode = pm_dict.get(line.payment_mode)
                    name = ''
                    if line.bank_id:
                        if name:
                            name += '-'
                        name += line.bank_id.name
                    if name:
                        name += '-'
                    name += payment_mode
                    if line.ref_no:
                        if name:
                            name += '-'
                        name += line.ref_no
                    new_payment_line_id = self.env['mbk_pms.contract.payment.line'].create(
                        {'contract_id': self.contract_id.id, 'service_id': line.service_id.id,
                         'name': name, 'note': line.name, 'ref_date': line.ref_date, 'payment_mode': line.payment_mode,
                         'bank_id': line.bank_id.id, 'amount': line.amount, 'ref_no': line.ref_no, 'category': 'other',
                         'depositing_bank_id': self.contract_id.depositing_bank_id.id, })
                    line.payment_line_id = new_payment_line_id
                if line.payment_line_id:
                    line.payment_line_id.state = 'received'
                    line.payment_line_id.last_activity_date = date.today()
                    line.payment_line_id.received_date = date.today()
                    if line.payment_line_id.service_id.category == 'deposit':
                        deposit = self.env['mbk_pms.contract.deposit.line'].search(
                            [('contract_id', '=', line.payment_line_id.contract_id.id),
                             ('deposit_id', '=', line.payment_line_id.service_id.id)])
                        if deposit and deposit.state:
                            deposit.state = 'received'
                            deposit.received_date = date.today()
                if line.payment_mode == 'chq':
                    chq_seq_no = self.env['ir.sequence'].next_by_code('mbk_pms.cheque_sequence')
                else:
                    chq_seq_no = line.id
                line.write({'reference_id': chq_seq_no})
                line.payment_line_id.write({'reference_id': chq_seq_no})

        else:
            raise UserError(_("Receipt details is missing"))

    def action_draft(self):
        self.write({'state': 'draft'})

    @api.depends('receipt_line_ids')
    def _compute_net_rent(self):
        for receipt in self:
            net_amount = 0.00

            for line in receipt.receipt_line_ids:
                net_amount += line.amount

            receipt.update({
                'net_amount': net_amount,
            })

    @api.onchange('contract_id')
    def onchange_contract_id(self):
        if self.contract_id:
            if self.contract_id.unit_id:
                self.unit_id = self.contract_id.unit_id
                self.property_id = self.contract_id.property_id
                self.tenant_id = self.contract_id.partner_id


class PMSPaymentCollectionLines(models.Model):
    _name = 'mbk_pms.payment_collection.line'
    _description = 'Payment Collection Lines'

    receipt_id = fields.Many2one('mbk_pms.payment_collection', string='Receipt Reference', required=True, ondelete='cascade', index=True, copy=False)
    service_id = fields.Many2one('mbk_pms.service', string='Service', required=True, domain="[('category', '=', 'service')]")
    name = fields.Text(string='Description', required=True)
    payment_line_id = fields.Many2one('mbk_pms.contract.payment.line', string='Payment Reference', domain="[('contract_id', '=', contract_id), ('state', 'in', ('draft', 'active'))]")
    payment_mode = fields.Selection(
        [('chq', 'Cheque'), ('cash', 'Cash'), ('transfer', 'Transfer'), ('credit', 'Credit')], string='Payment Mode',
        copy=False, default='chq')
    ref_date = fields.Date(string='Date', copy=False)
    ref_no = fields.Text(string='Cheque/Ref No', copy=False)
    bank_id = fields.Many2one('res.bank', string='Bank', copy=False)
    amount = fields.Float(string="Amount", default=0)
    contract_id = fields.Many2one(related='receipt_id.contract_id', string='Contract No')
    account_id = fields.Many2one('account.journal', string='Account', domain="[('type', 'in', ('bank','cash'))]")
    reference_id = fields.Char(string="Reference ID")

    @api.onchange('payment_line_id')
    def onchange_payment_line_id(self):
        self.payment_mode = self.payment_line_id.payment_mode
        self.ref_date = self.payment_line_id.ref_date
        self.ref_no = self.payment_line_id.ref_no
        self.bank_id = self.payment_line_id.bank_id
        self.amount = self.payment_line_id.amount
        self.name = self.payment_line_id.note

    @api.onchange('ref_no')
    def onchange_ref_no(self):
        if self.ref_no and self.payment_mode == 'chq':
            if not self.ref_no.isnumeric():
                self.ref_no = False
                raise UserError("Please enter valid numeric cheque number")
            if len(self.ref_no) != 6:
                self.ref_no = self.ref_no.zfill(6)

    @api.onchange('payment_mode')
    def onchange_payment_mode(self):
        if self.payment_mode:
            if self.payment_mode in ('cash', 'credit'):
                self.bank_id = False
                self.account_id = False
            elif self.payment_mode in ('chq', 'transfer'):
                if self.contract_id.bank_id:
                    self.bank_id = self.contract_id.bank

    @api.onchange('service_id')
    def onchange_service_id(self):
        if not self.name:
            self.name = self.service_id.description







