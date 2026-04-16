# -*- coding: utf-8 -*-

import ast
from datetime import date, datetime, timedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class PMSChequeRelease(models.Model):
    _name = 'mbk_pms.cheque_release'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'Cheque Release Voucher'

    name = fields.Char(string='Release No', tracking=True, default='Draft', copy=False)
    release_date = fields.Date(string='Release Date', default=fields.Date.context_today, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, copy=False, tracking=True, default='draft',
        help="""* When the release is created the status is \'Draft\'
                    \n* If the release is under confirmed, the status is \'Active\'.
                    \n* When user cancel release the status is \'cancelled\'.""")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    release_amount = fields.Monetary(string="Release Amount", readonly=True,
                                         compute='_compute_release_amount', store=True, default=0)
    note = fields.Text('Notes')
    owner_user_id = fields.Many2one('res.users', string='Created by User', default=lambda s: s.env.uid, copy=False)
    contract_id = fields.Many2one('mbk_pms.contract', string='Contract No', required=True, tracking=True)
    tenant_id = fields.Many2one(related='contract_id.partner_id', string='Tenant')
    unit_id = fields.Many2one(related='contract_id.unit_id', string='Unit No')
    contract_amount = fields.Monetary(related='contract_id.total_rent', string="Contract Amount")
    active = fields.Boolean(string="Active", default=True, tracking=True)
    release_line_ids = fields.One2many('mbk_pms.cheque_release.line', 'release_id',
                                           string='Release Lines', required=True,
                                           states={'cancel': [('readonly', True)], 'active': [('readonly', True)]},
                                           copy=True, auto_join=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id,
                                  store=True)

    @api.depends('release_line_ids')
    def _compute_release_amount(self):
        for release in self:
            release_amount = 0.00
            for line in release.release_line_ids:
                release_amount += line.amount
            release.update({
                'release_amount': release_amount,
            })

    def action_cancel(self):
        if self.filtered(lambda release: release.state == 'done'):
            raise UserError(_("Cannot cancel a release that is active."))
        else:
            self.write({'state': 'cancel'})

    def action_confirm(self):
        if self.release_line_ids:
            for line in self.release_line_ids:
                if line.payment_ref_id.state in ('received', 'active', 'hold', 'bounced'):
                    line.payment_ref_id.state = 'released'
                if line.payment_ref_id.service_id.category == 'deposit':
                    deposit = self.env['mbk_pms.contract.deposit.line'].search(
                        [('contract_id', '=',  line.contract_id.id),
                         ('deposit_id', '=',  line.service_id.id)])
                    if deposit and deposit.state:
                        deposit.state = 'released'
            self.write({'state': 'active'})
            release_no = self.env['ir.sequence'].next_by_code('mbk_pms.cheque_release')
            self.name = release_no
        else:
            raise UserError(_("Check release details is missing"))

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_load_existing_cheque(self):
        if self.state in ('draft'):
            self.release_line_ids.unlink()
            cheque_details = self.env['mbk_pms.contract.payment.line'].search(
                [('state', 'in', ('received', 'active', 'hold', 'bounced')), ('payment_mode', '=', 'chq'),
                 ('contract_id', '=', self.contract_id.id)], order='ref_date, ref_no')
            for line in cheque_details:
                self.env['mbk_pms.cheque_release.line'].create(
                    {'release_id': self.id, 'payment_ref_id': line.id, 'name': 'Released'})
        else:
            raise UserError("Can't process active release voucher")


class PMSReleaseLines(models.Model):
    _name = 'mbk_pms.cheque_release.line'
    _description = 'Release Cheque Details'

    release_id = fields.Many2one('mbk_pms.cheque_release', string='Release Reference', required=True,
                                     ondelete='cascade', index=True, copy=False)
    contract_id = fields.Many2one(related='release_id.contract_id', string='Contract No')
    payment_ref_id = fields.Many2one('mbk_pms.contract.payment.line', string='Payment Reference', domain="[('contract_id', '=', contract_id), ('state', 'in', ('received', 'active', 'hold', 'bounced')), ('payment_mode', '=', 'chq')]")
    service_id = fields.Many2one(related='payment_ref_id.service_id', string='Service')
    name = fields.Char(string='Remarks')
    note = fields.Text(related='payment_ref_id.note', string='Description')
    ref_date = fields.Date(related='payment_ref_id.ref_date', string='Date')
    payment_mode = fields.Selection(related='payment_ref_id.payment_mode', string='Payment Mode')
    ref_no = fields.Char(related='payment_ref_id.ref_no', string='Cheque No')
    bank_id = fields.Many2one(related='payment_ref_id.bank_id', string='Bank')
    amount = fields.Float(related='payment_ref_id.amount', string="Amount")
    state = fields.Char(string='State', copy=False, store=True)

    @api.onchange('payment_ref_id')
    def onchange_payment_ref_id(self):
        self.name = 'Released'

    @api.onchange('payment_ref_id')
    def onchange_payment_ref_id(self):
        if self.payment_ref_id:
            pm = self.payment_ref_id._fields['state'].selection
            state_dict = dict(pm)
            state = state_dict.get(self.payment_ref_id.state)
            self.state = state
        else:
            self.state = False
    

