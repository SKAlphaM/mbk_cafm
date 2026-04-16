# -*- coding: utf-8 -*-

import ast
from datetime import date, datetime, timedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class PMSChequeBounced(models.Model):
    _name = 'mbk_pms.cheque_bounced'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'Cheque Bounced Voucher'

    name = fields.Char(string='Document No', tracking=True, default='Draft', copy=False)
    bounced_date = fields.Date(string='Bounced Date', default=fields.Date.context_today, copy=False)
    as_on_date = fields.Date(string='As On Date', default=fields.Date.context_today, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, copy=False, tracking=True, default='draft',
        help="""* When the bounced is created the status is \'Draft\'
                    \n* If the bounced is under confirmed, the status is \'Active\'.
                    \n* When user cancel bounced the status is \'cancelled\'.""")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    net_amount = fields.Monetary(string="Total Amount", readonly=True, compute='_compute_net_amount',
                                 store=True, default=0)
    note = fields.Text('Notes')
    owner_user_id = fields.Many2one('res.users', string='Created by User', default=lambda s: s.env.uid, copy=False)
    journal_id = fields.Many2one('account.journal', string='Bank Account', domain="[('type', '=', 'bank')]", tracking=True, required=True)
    active = fields.Boolean(string="Active", default=True, tracking=True)
    bounced_line_ids = fields.One2many('mbk_pms.cheque_bounced.line', 'bounced_id', string='Bounced Cheque Lines',
                                       required=True,
                                       states={'cancel': [('readonly', True)], 'active': [('readonly', True)]},
                                       copy=True, auto_join=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id,
                                  store=True)

    @api.depends('bounced_line_ids')
    def _compute_net_rent(self):
        for bounced in self:
            net_amount = 0.00

            for line in bounced.bounced_line_ids:
                net_amount += line.amount

            bounced.update({
                'net_amount': net_amount,
            })

    @api.onchange('bounced_date')
    def onchange_contract_id(self):
        self.as_on_date = self.as_on_date

    @api.model
    def create(self, vals):
        # context: no_log, because subtype already handle this
        request = super(PMSChequeBounced, self).create(vals)
        return request

    def action_cancel(self):
        if self.filtered(lambda ticket: ticket.state == 'done'):
            raise UserError(_("Cannot cancel a bounced cheque voucher that is active."))
        else:
            self.write({'state': 'cancel'})

    def action_confirm(self):
        if self.bounced_line_ids:
            self.write({'state': 'active'})
            bounced_no = self.env['ir.sequence'].next_by_code('mbk_pms.cheque_bounced')
            self.name = bounced_no
            for line in self.bounced_line_ids:
                if line.payment_line_id:
                    if line.payment_line_id.state == 'deposited':
                        line.payment_line_id.state = 'bounced'
                        line.payment_line_id.last_activity_date = date.today()
                    else:
                        raise UserError("Invalid cheque status found! %s %s" % (line.payment_line_id.name, line.payment_line_id.state))
        else:
            raise UserError(_("bounced details is missing"))

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_load_bounced(self):
        if self.state in ('draft'):
            self.bounced_line_ids.unlink()
            chq_filter = [('state', '=', 'deposited'), ('payment_mode', '=', 'chq'), ('deposited_date', '<=', self.as_on_date)]
            if self.state_id:
                chq_filter.append(('state_id', '=', self.state_id.id))
            if self.property_id:
                chq_filter.append(('property_id', '=', self.property_id.id))
            if self.tenant_id:
                chq_filter.append(('tenant_id', '=', self.tenant_id.id))

            cheque_details = self.env['mbk_pms.contract.payment.line'].search(chq_filter, order='ref_date,contract_id')
            for line in cheque_details:
                self.env['mbk_pms.cheque_bounced.line'].create(
                    {'bounced_id': self.id, 'name': line.name, 'payment_line_id': line.id,
                     'payment_mode': line.payment_mode, 'ref_date': line.ref_date, 'ref_no': line.ref_no,
                     'bank_id': line.bank_id.id, 'amount': line.amount, })
        else:
            raise UserError("Can't process active bounced voucher")


class PMSChequeBouncedLines(models.Model):
    _name = 'mbk_pms.cheque_bounced.line'
    _description = 'Cheque Bounced Lines'

    name = fields.Char(string='Description', required=True)
    bounced_id = fields.Many2one('mbk_pms.cheque_bounced', string='bounced Reference', required=True,
                                 ondelete='cascade', index=True, copy=False)
    journal_id = fields.Many2one(related='bounced_id.journal_id', string='Bank Account')
    as_on_date = fields.Date(related='bounced_id.as_on_date', string='As On Date')
    payment_line_id = fields.Many2one('mbk_pms.contract.payment.line', string='Payment Reference',
                                      domain="[('state', '=', 'deposited'), ('payment_mode', '=', 'chq'), ('ref_date', '<=', as_on_date), ('depositing_bank_id', '=', journal_id)]")
    service_id = fields.Many2one(related='payment_line_id.service_id', string='Service')
    note = fields.Text(related='payment_line_id.note', string='Remarks')
    ref_date = fields.Date(related='payment_line_id.ref_date', string='Date')
    payment_mode = fields.Selection(related='payment_line_id.payment_mode', string='Payment Mode')
    ref_no = fields.Char(related='payment_line_id.ref_no', string='Cheque No')
    bank_id = fields.Many2one(related='payment_line_id.bank_id', string='Bank')
    amount = fields.Float(related='payment_line_id.amount', string="Amount")
    contract_id = fields.Many2one(related='payment_line_id.contract_id', string='Contract No')
    tenant_id = fields.Many2one(related='payment_line_id.tenant_id', string='Tenant No')
    unit_id = fields.Many2one(related='payment_line_id.unit_id', string='Unit No')
    property_id = fields.Many2one(related='payment_line_id.property_id', string='Property')
