# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class GeneralApproval(models.Model):
    _name = 'general.approval'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'General Approval'

    name = fields.Char(string='Approval No', tracking=True, default='Draft', copy=False)
    voucher_date = fields.Date(string='Date', default=fields.Date.context_today, copy=False)
    state = fields.Selection([('draft', 'Draft'), ('active', 'Active'), ('cancel', 'Cancelled'), ],
                             string='Status', readonly=True, copy=False, tracking=True, default='draft',
                             help="""Status of the Voucher""")
    portfolio = fields.Selection(related='contract_id.portfolio', string='Portfolio')
    tenant_type = fields.Selection([('comm', 'Commercial'), ('resident', 'Residential'), ],
                                   string='Tenant Type', copy=False, tracking=True, default=False,
                                   help="""Type Of Tenant""")
    details_of_request = fields.Text(string='Details of Request', copy=False)
    reasons = fields.Text(string='Reason/Justification', copy=False)
    contract_id = fields.Many2one('mbk_pms.contract', string='Contract No', required=True, tracking=True,
                                  domain="[('state', '=', 'open')]")
    tenant_id = fields.Many2one(related='contract_id.partner_id', string='Tenant')
    bldg_no = fields.Many2one(related='contract_id.unit_id', string='Building No.')
    state_id = fields.Many2one(related='contract_id.state_id', string='Location')
    company_id = fields.Many2one(related='contract_id.company_id', string='Lessor')
    unit_no = fields.Many2one(related='contract_id.unit_id.rn_id', string='Unit No.')
    contract_start_date = fields.Date(related='contract_id.start_date', string='Contract Start Date',
                                      help="Contract Valid from date.", copy=False)
    contract_expiry_date = fields.Date(related='contract_id.expiry_date', string='Contract Expiration Date',
                                       help="Contract Valid upto.", copy=False)
    current_rent = fields.Float(string='Current Rent', copy=False, compute='compute_rent_amt', store=True)
    previous_rent = fields.Float(string='Previous Rent', copy=False, compute='compute_rent_amt', store=True)
    security_deposit = fields.Float(string='Security Deposit', copy=False, compute='compute_rent_amt', store=True)

    def action_confirm(self):
        if self.name == 'Draft':
            request_no = self.env['ir.sequence'].next_by_code('code.general.approval')
            self.name = request_no
        self.state = 'active'

    def action_cancel(self):
        self.state = 'cancel'

    def action_set_draft(self):
        self.state = 'draft'

    @api.depends('contract_id')
    @api.onchange('contract_id')
    def compute_rent_amt(self):
        if self.contract_id.payment_line_ids:
            self.current_rent = sum(self.contract_id.payment_line_ids.filtered(lambda payment:
                                                                               payment.state in ('received', 'deposited', 'cleared')).mapped('amount'))
            self.security_deposit = self.contract_id.total_deposit
        if self.contract_id.parent_contract_id:
            self.previous_rent = self.contract_id.parent_contract_id.total_rent
