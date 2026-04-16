# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta


class PMSChequeAction(models.Model):
    _name = 'mbk_pms.process_bounced'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'Process Bounced Cheque'

    name = fields.Char(string=' Document No', tracking=True, default='Draft', copy=False)
    request_date = fields.Date(string='Process Date', default=fields.Date.context_today, copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'To Approve'),
        ('refuse', 'Rejected'),
        ('active', 'Active'),
        ('close', 'Expired'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, copy=False, tracking=True, default='draft')
    contract_id = fields.Many2one('mbk_pms.contract', string='Contract No', required=True, tracking=True, domain="[('state', '=', 'open')]")
    tenant_id = fields.Many2one(related='contract_id.partner_id', string='Tenant')
    payment_line_id = fields.Many2one('mbk_pms.contract.payment.line', string='Payment Reference', required=True,
                                      domain="[('contract_id', '=', contract_id), ('state', '=', 'bounced'), ('payment_mode', '=', 'chq')]")
    payment_mode = fields.Selection(related='payment_line_id.payment_mode', string='Payment Mode')
    ref_date = fields.Date(related='payment_line_id.ref_date', string='Cheque Date', copy=False)
    ref_no = fields.Char(related='payment_line_id.ref_no', string='Cheque No', copy=False)
    bank_id = fields.Many2one(related='payment_line_id.bank_id', string='Bank', copy=False)
    amount = fields.Float(related='payment_line_id.amount', string="Amount")
    action = fields.Selection([('deposited', 'Re-deposit'), ('legal', 'Transfer to Legal')], string='Action', copy=False, default='deposit')
    note = fields.Text('Notes', required=True)
    owner_user_id = fields.Many2one('res.users', string='Created by User', default=lambda s: s.env.uid, copy=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    unit_id = fields.Many2one(related='contract_id.unit_id', string='Unit No')
    contract_amount = fields.Monetary(related='contract_id.net_amount', string="Contract Amount")
    active = fields.Boolean(string="Active", default=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id,
                                  store=True)
    
    @api.model
    def create(self, vals):
        # context: no_log, because subtype already handle this
        request = super(PMSChequeAction, self).create(vals)
        return request

    def action_cancel(self):
        if self.filtered(lambda action: action.state == 'done'):
            raise UserError(_("Cannot cancel a deposit that is active."))
        else:
            self.write({'state': 'cancel'})

    def action_draft(self):
        if self.filtered(lambda contract: contract.state == 'active'):
            raise UserError("Cannot draft a active Cheque Hold Request.")
        else:
            self.write({'state': 'draft'})

    def action_confirm(self):
        if self.filtered(lambda contract: contract.state == 'draft' and contract.action):
            if self.name == 'Draft':
                request_no = self.env['ir.sequence'].next_by_code('mbk_pms.process_bounced')
                self.name = request_no
            self.write({'state': 'active'})
            self.payment_line_id.state = self.action
            self.payment_line_id.last_activity_date = date.today()
        else:
            raise UserError("Invalid Status %s" % self.state)
