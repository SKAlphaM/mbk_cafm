# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class FurnitureMove(models.Model):
    _name = 'furniture.move'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'Furniture Move'

    name = fields.Char(string='Voucher No', tracking=True, default='Draft', copy=False)
    voucher_date = fields.Date(string='Date', default=fields.Date.context_today, copy=False)
    start_date = fields.Date(string='Start Date', help="Voucher Valid from date.", copy=False)
    expiry_date = fields.Date(string='Expiration Date', help="Voucher Valid upto.", copy=False)
    state = fields.Selection([('draft', 'Draft'),('active', 'Active'),('cancel', 'Cancelled'),], 
        string='Status', readonly=True, copy=False, tracking=True, default='draft',
        help="""Status of the Voucher""")
    voucher_type = fields.Selection([('move_in', 'Move In'),('move_out', 'Move Out'),
        ('replacement', 'Replacement'),('transfer_luggage', 'Transfer Luggage')], 
        string='Type', copy=False, tracking=True, default=False,
        help="""Status of the Voucher""")
    note = fields.Text(string='Notes', copy=False)
    contract_id = fields.Many2one('mbk_pms.contract', string='Contract No', required=True, tracking=True, 
        domain="[('state', '=', 'open')]")
    tenant_id = fields.Many2one(related='contract_id.partner_id', string='Tenant')
    contact_no = fields.Char(related='contract_id.partner_id.mobile', string='Contact')
    unit_id = fields.Many2one(related='contract_id.unit_id', string='Unit')
    property_id = fields.Many2one(related='contract_id.property_id', string='Property')
    contract_start_date = fields.Date(related='contract_id.start_date', string='Contract Start Date')
    contract_expiry_date = fields.Date(related='contract_id.expiry_date', string='Contract Expiration Date')



    def action_confirm(self):
        if self.name == 'Draft':
            request_no = self.env['ir.sequence'].next_by_code('code.furniture.move')
            self.name = request_no
        self.state ='active'

    def action_cancel(self):
        self.state ='cancel'
