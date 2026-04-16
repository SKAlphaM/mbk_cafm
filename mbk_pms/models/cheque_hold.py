# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta


class PMSChequeHold(models.Model):
    _name = 'mbk_pms.cheque_hold'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'Cheque Hold Request'

    name = fields.Char(string='Cheque Hold Request No', tracking=True, default='Draft', copy=False)
    request_date = fields.Date(string='Request Date', default=fields.Date.context_today, copy=False)
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
                                      domain="[('contract_id', '=', contract_id), ('state', '=', 'received'), ('payment_mode', '=', 'chq')]")
    payment_mode = fields.Selection(
        [('chq', 'Cheque'), ('cash', 'Cash'), ('transfer', 'Transfer'), ('credit', 'Credit')], string='Payment Mode',
        copy=False, default='chq')
    ref_date = fields.Date(related='payment_line_id.ref_date', string='Cheque Date', copy=False)
    ref_no = fields.Char(related='payment_line_id.ref_no', string='Cheque No', copy=False)
    bank_id = fields.Many2one(related='payment_line_id.bank_id', string='Bank', copy=False)
    amount = fields.Float(related='payment_line_id.amount', string="Amount")
    hold_upto_date = fields.Date(string='Hold Upto Date', copy=False)
    hold_upto_days = fields.Integer(string='Hold Upto Days', copy=False, readonly=True, store=True)
    note = fields.Text('Notes', required=True)
    owner_user_id = fields.Many2one('res.users', string='Created by User', default=lambda s: s.env.uid, copy=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    unit_id = fields.Many2one(related='contract_id.unit_id', string='Unit No')
    contract_amount = fields.Monetary(related='contract_id.net_amount', string="Contract Amount")
    active = fields.Boolean(string="Active", default=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id,
                                  store=True)

    @api.onchange('ref_date')
    def onchange_ref_date(self):
        if self.ref_date:
            self.hold_upto_date = self.ref_date + relativedelta(days=14)

    @api.onchange('hold_upto_date')
    def onchange_hold_upto_date(self):
        if self.ref_date and self.hold_upto_date:
            self.hold_upto_days = (self.hold_upto_date-self.ref_date).days+1

    @api.onchange('contract_id')
    def onchange_contract_id(self):
        if self.tenant_id:
            self.tenant_id = self.contract_id.partner_id

    @api.model
    def create(self, vals):
        # context: no_log, because subtype already handle this
        request = super(PMSChequeHold, self).create(vals)
        return request

    def action_cancel(self):
        if self.filtered(lambda ticket: ticket.state == 'done'):
            raise UserError(_("Cannot cancel a deposit that is active."))
        else:
            self.write({'state': 'cancel'})

    def action_confirm(self, comment):
        self.write({'state': 'active'})
        self.payment_line_id.state = 'hold'
        self.payment_line_id.last_activity_date = date.today()
        self.activity_feedback(['mbk_pms.mail_act_pms_chq_hold_approval'], feedback=comment)

    def action_reject(self, comment):
        if self.filtered(lambda chq_hold: chq_hold.state == 'confirm'):
            self.write({'state': 'refuse'})
            self.activity_unlink(['mbk_pms.mail_act_pms_chq_hold_approval'])

    def action_draft(self):
        if self.filtered(lambda contract: contract.state == 'active'):
            raise UserError("Cannot draft a active Cheque Hold Request.")
        else:
            self.write({'state': 'draft'})

    def action_done(self, comment):
        approval_user_id = self.env['ir.config_parameter'].get_param('mbk_pms_lease_offer_approver_id')
        if self.filtered(lambda contract: contract.state == 'draft'):
            if self.name == 'Draft':
                request_no = self.env['ir.sequence'].next_by_code('mbk_pms.cheque_hold')
                self.name = request_no
            self.write({'state': 'confirm'})
            self.activity_schedule('mbk_pms.mail_act_pms_chq_hold_approval', fields.Datetime.now().date(),
                                   note="To Approve Cheque Hold Request " + self.name + '\n' + comment,
                                   user_id=approval_user_id or self.owner_user_id.id or self.env.uid)
        else:
            raise UserError("Invalid Status %s" % self.state)

    def action_done_update_state_wizard(self):
        return {
            'name': 'Update Status',
            'res_model': 'mbk_pms.chq_hold_update_state_wizard',
            'view_mode': 'form',
            'context': {'default_cheque_hold_id': self.id, 'default_status': 'done', 'default_label_name': 'Submit for Approval', 'default_comment': self.note},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_confirm_update_state_wizard(self):
        return {
            'name': 'Update Status',
            'res_model': 'mbk_pms.chq_hold_update_state_wizard',
            'view_mode': 'form',
            'context': {'default_cheque_hold_id': self.id, 'default_status': 'confirm', 'default_label_name': 'Approve'},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_cancel_update_state_wizard(self):
        return {
            'name': 'Update Status',
            'res_model': 'mbk_pms.chq_hold_update_state_wizard',
            'view_mode': 'form',
            'context': {'default_cheque_hold_id': self.id, 'default_status': 'cancel', 'default_label_name': 'Cancel'},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_reject_update_state_wizard(self):
        return {
            'name': 'Update Status',
            'res_model': 'mbk_pms.chq_hold_update_state_wizard',
            'view_mode': 'form',
            'context': {'default_cheque_hold_id': self.id, 'default_status': 'refuse', 'default_label_name': 'Reject'},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    @api.model
    def _cron_update_hold_cheques(self):
        """
            Remove hold cheque based on expiry date
        """
        today = date.today()
        for chq_hold in self.search([('state', '=', 'active'), ('hold_upto_date', '<', today)]):
            if chq_hold.payment_line_id:
                chq_hold.state = 'close'
                if chq_hold.payment_line_id.state == 'hold':
                    chq_hold.payment_line_id.state = 'received'
                    chq_hold.payment_line_id.last_activity_date = date.today()

