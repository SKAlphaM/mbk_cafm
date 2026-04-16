# -*- coding: utf-8 -*-

import ast
from datetime import date, datetime, timedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class PMSChequeReplacement(models.Model):
    _name = 'mbk_pms.cheque_replacement'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'Cheque Replacement Voucher'

    name = fields.Char(string='Replacement No', tracking=True, default='Draft', copy=False)
    replacement_date = fields.Date(string='Replacement Date', default=fields.Date.context_today, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, copy=False, tracking=True, default='draft',
        help="""* When the replacement is created the status is \'Draft\'
                    \n* If the replacement is under confirmed, the status is \'Active\'.
                    \n* When user cancel replacement the status is \'cancelled\'.""")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    new_amount = fields.Monetary(string="Total Amount", readonly=True, compute='_compute_replacement_amount',
                                     store=True, default=0)
    replacement_amount = fields.Monetary(string="Replacement Amount", readonly=True,
                                         compute='_compute_replacement_amount', store=True, default=0)
    note = fields.Text('Notes')
    owner_user_id = fields.Many2one('res.users', string='Created by User', default=lambda s: s.env.uid, copy=False)
    contract_id = fields.Many2one('mbk_pms.contract', string='Contract No', required=True, tracking=True, domain="[('state', '=', 'open')]")
    tenant_id = fields.Many2one(related='contract_id.partner_id', string='Tenant')
    unit_id = fields.Many2one(related='contract_id.unit_id', string='Unit No')
    contract_amount = fields.Monetary(related='contract_id.net_amount', string="Contract Amount")
    active = fields.Boolean(string="Active", default=True, tracking=True)
    replacement_line_ids = fields.One2many('mbk_pms.cheque_replacement.line', 'replacement_id',
                                           string='Replacement Lines', required=True,
                                           states={'cancel': [('readonly', True)], 'active': [('readonly', True)]},
                                           copy=True, auto_join=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id,
                                  store=True)

    @api.depends('replacement_line_ids')
    def _compute_replacement_amount(self):
        for replacement in self:
            replacement_amount = 0.00
            new_amount = 0.00
            for line in replacement.replacement_line_ids:
                replacement_amount += line.amount
                new_amount += line.new_amount
            replacement.update({
                'replacement_amount': replacement_amount,
                'new_amount': new_amount,
            })

    @api.model
    def create(self, vals):
        # context: no_log, because subtype already handle this
        request = super(PMSChequeReplacement, self).create(vals)
        return request

    def action_cancel(self):
        if self.filtered(lambda replacement: replacement.state == 'done'):
            raise UserError(_("Cannot cancel a replacement that is active."))
        else:
            self.write({'state': 'cancel'})

    def action_confirm(self):
        if self.replacement_line_ids:
            if self.replacement_amount != self.new_amount:
                raise UserError(_("replacement cheque amount are not matching %d %d") % (self.replacement_amount, self.new_amount))
            else:
                payment_ref_id = False
                for line in self.replacement_line_ids:
                    if line.payment_ref_id:
                        payment_ref_id = line.payment_ref_id

                    if line.payment_ref_id.state in ('received', 'active', 'hold', 'bounced'):
                        line.payment_ref_id.state = 'replaced'
                        line.payment_ref_id.last_activity_date = date.today()
                    elif not line.payment_ref_id:
                        print("Info: Payment line not mentioned for line and previous line carry forwarded", payment_ref_id.name)
                    else:
                        raise UserError(_("invalid  cheque status for replacing cheque : %s") % (line.payment_ref_id.state))

                    if not line.payment_ref_id and not payment_ref_id:
                        raise UserError(("Parent payment mode not defined for : %s") % (line.new_name))
                    if line.payment_ref_id:
                        new_payment_line_id = self.env['mbk_pms.contract.payment.line'].create({
                            'name': line.new_name,
                            'note': line.note,
                            'contract_id': line.contract_id.id,
                            'service_id': line.service_id.id,
                            'ref_date': line.new_ref_date,
                            'ref_no': line.new_ref_no,
                            'bank_id': line.new_bank_id.id,
                            'depositing_bank_id': line.journal_id.id,
                            'from_date': line.from_date,
                            'to_date': line.to_date,
                            'days': line.days,
                            'payment_mode': line.new_payment_mode,
                            'amount': line.new_amount,
                            'company_id': self.company_id.id,
                            'parent_id': line.payment_ref_id.id,
                            'received_date': self.replacement_date,
                            'last_activity_date': date.today(),
                            'state': 'received', })
                        line.payment_line_id = new_payment_line_id
                    else:
                        new_payment_line_id = self.env['mbk_pms.contract.payment.line'].create({
                            'name': line.new_name,
                            'note': payment_ref_id.note,
                            'contract_id': payment_ref_id.contract_id.id,
                            'service_id': payment_ref_id.service_id.id,
                            'ref_date': line.new_ref_date,
                            'ref_no': line.new_ref_no,
                            'bank_id': line.new_bank_id.id,
                            'depositing_bank_id': line.journal_id.id,
                            'payment_mode': line.new_payment_mode,
                            'amount': line.new_amount,
                            'company_id': self.company_id.id,
                            'parent_id': payment_ref_id.id,
                            'received_date': self.replacement_date,
                            'last_activity_date': date.today(),
                            'state': 'received', })
                        line.payment_line_id = new_payment_line_id

                self.write({'state': 'active'})
                replacement_no = self.env['ir.sequence'].next_by_code('mbk_pms.cheque_replacement')
                self.name = replacement_no
        else:
            raise UserError(_("replacement details is missing"))

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_load_existing_cheque(self):
        if self.state in ('draft'):
            self.replacement_line_ids.unlink()
            cheque_details = self.env['mbk_pms.contract.payment.line'].search(
                [('state', 'in', ('received', 'active', 'hold', 'bounced')), ('payment_mode', '=', 'chq'),
                 ('contract_id', '=', self.contract_id.id)], order='ref_date, ref_no')
            for line in cheque_details:
                self.env['mbk_pms.cheque_replacement.line'].create(
                    {'replacement_id': self.id, 'payment_ref_id': line.id,
                     'new_ref_date': line.ref_date, 'new_bank_id': line.bank_id.id, 'new_amount': line.amount, })
        else:
            raise UserError("Can't process active replacement voucher")


class PMSReplacementLines(models.Model):
    _name = 'mbk_pms.cheque_replacement.line'
    _description = 'Replacement Cheque Details'

    replacement_id = fields.Many2one('mbk_pms.cheque_replacement', string='Replacement Reference', required=True,
                                     ondelete='cascade', index=True, copy=False)
    contract_id = fields.Many2one(related='replacement_id.contract_id', string='Contract No')
    payment_ref_id = fields.Many2one('mbk_pms.contract.payment.line', string='Payment Reference', domain="[('contract_id', '=', contract_id)]")
    service_id = fields.Many2one(related='payment_ref_id.service_id', string='Service')
    name = fields.Char(related='payment_ref_id.name', string='Description')
    note = fields.Text(related='payment_ref_id.note', string='Remarks')
    ref_date = fields.Date(related='payment_ref_id.ref_date', string='Date')
    payment_mode = fields.Selection(related='payment_ref_id.payment_mode', string='Payment Mode')
    ref_no = fields.Char(related='payment_ref_id.ref_no', string='Cheque No')
    bank_id = fields.Many2one(related='payment_ref_id.bank_id', string='Bank')
    amount = fields.Float(related='payment_ref_id.amount', string="Amount")
    chq_type = fields.Selection(related='payment_ref_id.chq_type', string='Cheque Type', copy=False,
                                help="""Cheque Type""")
    from_date = fields.Date(related='payment_ref_id.from_date', string='From Date')
    to_date = fields.Date(related='payment_ref_id.to_date', string='To Date')
    days = fields.Float(related='payment_ref_id.days', string='Days')
    depositing_bank_id = fields.Many2one(related='payment_ref_id.depositing_bank_id', string='Depositing Bank')
    state = fields.Selection(related='payment_ref_id.state', string='Status')
    new_payment_mode = fields.Selection([('chq', 'Cheque'), ('cash', 'Cash'), ('transfer', 'Transfer'), ('credit', 'Credit')],
                                        string='New Payment Mode', copy=False, default='chq')
    new_ref_date = fields.Date(string='New Date', copy=False, required=True)
    new_ref_no = fields.Char(string='New Cheque/Ref No', copy=False)
    new_bank_id = fields.Many2one('res.bank', string='New Bank', copy=False)
    new_amount = fields.Float(string="New Amount", default=0, required=True)
    new_name = fields.Char(string="New Description", default=0)
    new_account_type = fields.Char(string='Account', copy=False, readonly=True)
    new_chq_type = fields.Selection([('blank', 'Blank Dated Cheque'), ('dated', 'Dated Cheque'), ], string='New Cheque Type', copy=False)
    journal_id = fields.Many2one('account.journal', string='New Account', domain="[('type', '=', new_account_type)]")
    payment_line_id = fields.Many2one('mbk_pms.contract.payment.line', string='New Payment Reference', readonly=True)

    @api.onchange('payment_ref_id')
    def onchange_payment_ref_id(self):
        self.new_ref_date = self.ref_date
        self.new_amount = self.amount
        self.new_payment_mode = self.payment_mode
        self.new_chq_type = self.chq_type

    @api.onchange('new_payment_mode', 'new_ref_no', 'new_bank_id')
    def onchange_service_id(self):
        if self.new_payment_mode and self.new_payment_mode in ('chq', 'transfer'):
            self.new_account_type = 'bank'
        elif self.new_payment_mode == 'cash':
            self.new_account_type = 'cash'
        else:
            self.new_account_type = 'general'

        pm = self._fields['new_payment_mode'].selection
        pm_dict = dict(pm)
        payment_mode = pm_dict.get(self.new_payment_mode)
        name = ''

        if self.new_ref_no and self.new_payment_mode == 'chq':
            if not self.new_ref_no.isnumeric():
                self.new_ref_no = False
                raise UserError("Please enter valid numeric cheque number")
            if len(self.new_ref_no) != 6:
                self.new_ref_no = self.new_ref_no.zfill(6)

        if self.payment_ref_id and self.payment_ref_id.contract_id.name != 'Draft':
            name += self.payment_ref_id.contract_id.name
        if self.new_bank_id:
            if name:
                name += '-'
            name += self.new_bank_id.name
        if payment_mode:
            if name:
                name += '-'
            name += payment_mode
        if self.new_ref_no:
            if name:
                name += '-'
            name += self.new_ref_no
        self.new_name = name

