# -*- coding: utf-8 -*-

from odoo import models, fields


class PmsServices(models.Model):
    _name = 'mbk_pms.service'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'Lease Services'
    _order = 'sequence,id'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    category = fields.Selection([('rent', 'Rental Service'), ('service', 'Services'), ('deposit', 'Security Deposit'), ('ded', 'Deductions')], string='Service Category', copy=False, default='service')
    price = fields.Float(string="Price")
    is_one_time = fields.Boolean(string="One Time", default=True)
    is_separate_chq = fields.Boolean(string="Separate Cheque", default=True)
    is_tax = fields.Boolean(string="Tax", default=True)
    on_renewal = fields.Boolean(string="On renewal")
    bank_account_id = fields.Many2one('account.journal', string='Bank Account', domain="[('type', '=', 'bank')]", tracking=True)
    account_id = fields.Many2one('account.account', string='Sales Account', tracking=True)
    advance_account_id = fields.Many2one('account.account', string='Advance Account', tracking=True)
    description = fields.Text(string='Description')
    ref_id = fields.Integer(string='Reference ID')
    active = fields.Boolean(string="Active", default=True)
    arabic_name = fields.Char(string='Arabic Name', copy=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    sequence = fields.Integer(string="Sequence ", default=10)

