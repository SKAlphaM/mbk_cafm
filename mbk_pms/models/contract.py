# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class PmsContract(models.Model):
    _name = 'mbk_pms.contract'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'Lease Contract'

    name = fields.Char(string='Tenancy Contract No', tracking=True, default='Draft', copy=False)
    contract_date = fields.Date(string='Contract Date', default=fields.Date.context_today, copy=False)
    partner_id = fields.Many2one(
        'res.partner', string='Tenant', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        required=True, change_default=True, index=True, tracking=1,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", )
    partner_contact_id = fields.Many2one(
        'res.partner', string='Tenancy Contract Address', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('non-renewal', 'Non Renewal'),
        ('confirm', 'To Approve'),
        ('open', 'Running'),
        ('hold', 'Hold'),
        ('refuse', 'Rejected'),
        ('close', 'Expired'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, copy=False, tracking=True, default='draft',
        help="""Status of the contract""")
    start_date = fields.Date(string='Start Date', help="Contract Valid from date.", copy=False)
    expiry_date = fields.Date(string='Expiration Date', help="Contract Valid upto.", copy=False)
    is_approval_required = fields.Boolean(string='Approval Required', default=1)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, copy=False)
    unit_id = fields.Many2one('mbk_pms.unit', string='Unit', copy=False, readonly=True, )
    property_id = fields.Many2one(related='unit_id.property_id', string='Property')
    currency_id = fields.Many2one('res.currency', string='Currency', default=127, store=True)
    owner_user_id = fields.Many2one('res.users', string='Sales Person', default=lambda s: s.env.uid, copy=False)
    mobile = fields.Char(related='partner_id.mobile', string='Mobile No', copy=False, store=True)
    email = fields.Char(related='partner_id.email', string='Email', copy=False, store=True)
    state_id = fields.Many2one('res.country.state', string='Emirate')
    payment_terms = fields.Selection(
        [('1', '1 Times'), ('2', '2 Times'), ('3', '3 Times'), ('4', '4 Times'), ('5', '5 Times'),
         ('6', '6 Times'), ('7', '7 Times'), ('8', '8 Times'), ('9', '9 Times'), ('10', '10 Times'), ('11', '11 Times'),
         ('12', '12 Times'), ], string='Payment Terms', copy=False, tracking=True, default='4',
        help="""Status of the contract""")
    note = fields.Text(string='Notes', copy=False)
    payment_note = fields.Text(string='Payment Notes', copy=False)
    bank_id = fields.Many2one('res.bank', string='Bank', copy=False)
    depositing_bank_id = fields.Many2one('account.journal', string='Depositing Bank', domain="[('type', '=', 'bank')]",
                                         tracking=True)
    receipt_id = fields.Many2one('mbk_pms.payment_collection', string='Receipt No', copy=False)
    ref_id = fields.Integer(string='Reference ID', copy=False)
    is_tax = fields.Boolean(string="Tax")
    is_include_service = fields.Boolean(string="Service charges with first payment", default=False)
    lease_offer_id = fields.Many2one('mbk_pms.lease_offer', string='Lease Offer Reference', copy=False, readonly='True')
    breaking_request_id = fields.Many2one('mbk_pms.break_request', string='Breaking Request', copy=False, readonly='True')
    breaking_contract_id = fields.Many2one('mbk_pms.break_contract', string='Break Contract', copy=False, readonly='True')
    renewal_offer_id = fields.Many2one('mbk_pms.renewal_offer', string='Renewal Offer Reference', copy=False, readonly='True')
    renewed_contract_id = fields.Many2one('mbk_pms.contract', string='Renewed Contract', copy=False, readonly='True')
    parent_contract_id = fields.Many2one('mbk_pms.contract', string='Parent Contract', copy=False, readonly='True')
    active = fields.Boolean(string="Active", default=True, tracking=True, copy=False)
    units = fields.Char(string='Units', copy=False, store=True, readonly=True, compute='_compute_net_rent')
    unit_line_ids = fields.One2many('mbk_pms.contract.unit.line', 'contract_id', string='Unit Lines', readonly=True,
                                    states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, copy=False, auto_join=True)
    service_line_ids = fields.One2many('mbk_pms.contract.service.line', 'contract_id', string='Service Lines',
                                       states={'cancel': [('readonly', True)], 'close': [('readonly', True)]},
                                       copy=False, auto_join=True)
    deposit_line_ids = fields.One2many('mbk_pms.contract.deposit.line', 'contract_id', string='Deposit Lines',
                                       states={'cancel': [('readonly', True)], 'close': [('readonly', True)]},
                                       copy=False, auto_join=True)
    payment_line_ids = fields.One2many('mbk_pms.contract.payment.line', 'contract_id', string='Payment Schedule Lines', domain="[('category', '=', 'main')]",
                                       states={'cancel': [('readonly', True)], 'close': [('readonly', True)]},
                                       copy=False, auto_join=True)
    total_rent = fields.Monetary(string="Total Rent", readonly=True, compute='_compute_net_rent', store=True, default=0)
    total_service = fields.Monetary(string="Total Service", readonly=True, compute='_compute_net_service', store=True,
                                    default=0)
    total_deposit = fields.Monetary(string="Total Deposit", readonly=True, compute='_compute_net_deposit', store=True,
                                    default=0)
    total_rent_tax = fields.Monetary(string="Total Rent Tax", readonly=True, compute='_compute_net_rent', store=True,
                                     default=0)
    total_service_tax = fields.Monetary(string="Total Service Tax", readonly=True, compute='_compute_net_service',
                                        store=True, default=0)
    net_tax = fields.Monetary(string="Total Tax", readonly=True, store=True, default=0)
    net_rent_amount = fields.Monetary(string="Net Rent Amount", readonly=True, compute='_compute_net_rent', store=True,
                                      default=0)
    net_service_amount = fields.Monetary(string="Net Service Amount", readonly=True, compute='_compute_net_service',
                                         store=True, default=0)
    net_amount = fields.Monetary(string="Net Amount", readonly=True, store=True, default=0)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.partner_contact_id = self.partner_id
            if self.partner_id.state_id:
                self.state_id = self.partner_id.state_id
        else:
            self.partner_contact_id = False

    @api.onchange('contract_date')
    def onchange_contract_date(self):
        if self.contract_date:
            self.start_date = self.contract_date

    @api.onchange('start_date')
    def onchange_start_date(self):
        if self.start_date:
            self.expiry_date = self.start_date + relativedelta(years=1, days=-1)

    @api.onchange('net_rent_amount', 'net_service_amount', 'total_deposit')
    def onchange_net_amount(self):
        self.net_amount = self.net_rent_amount + self.net_service_amount + self.total_deposit

    @api.onchange('total_rent_tax', 'total_service_tax')
    def onchange_net_tax(self):
        self.net_tax = self.total_rent_tax + self.total_service_tax

    @api.depends('unit_line_ids')
    def _compute_net_rent(self):
        for contract in self:
            total_rent = 0.00
            total_rent_tax = 0.00
            net_rent_amount = 0.00
            units = ''

            if contract.unit_line_ids:
                if contract.unit_line_ids[0].unit_id:
                    contract.unit_id = contract.unit_line_ids[0].unit_id
                    if contract.unit_id.use_type == 'com':
                        contract.is_tax = True
                    else:
                        contract.is_tax = False
            else:
                unit_id = False

            for line in contract.unit_line_ids:
                total_rent += line.agreement_rent
                total_rent_tax += line.tax_amount
                net_rent_amount += line.net_rent
                if units == '':
                    units = line.unit_id.name
                else:
                    units = units + ', ' + line.unit_id.name

            contract.update({
                'total_rent': total_rent,
                'total_rent_tax': total_rent_tax,
                'net_rent_amount': net_rent_amount,
                'units': units,
            })

    @api.depends('service_line_ids')
    def _compute_net_service(self):
        for contract in self:
            total_service = 0.00
            total_service_tax = 0.00
            net_service_amount = 0.00

            for line in contract.service_line_ids:
                total_service += line.amount
                total_service_tax += line.tax_amount
                net_service_amount += line.net_amount

            contract.update({
                'total_service': total_service,
                'total_service_tax': total_service_tax,
                'net_service_amount': net_service_amount,
            })

    @api.depends('deposit_line_ids')
    def _compute_net_deposit(self):
        for contract in self:
            total_deposit = 0.00

            for line in contract.deposit_line_ids:
                total_deposit += line.amount

            contract.update({
                'total_deposit': total_deposit,
            })

    @api.model
    def create(self, vals):
        # context: no_log, because subtype already handle this
        contract = super(PmsContract, self).create(vals)
        return contract

    def name_get(self):
        return [(rec.id, "[%s] %s" % (rec.name, rec.units)) for rec in self]

    def action_done(self, comment):
        approval_user_id = self.env['ir.config_parameter'].get_param('mbk_pms_lease_offer_approver_id')
        if self.filtered(lambda contract: contract.state == 'draft'):
            self.write({'state': 'confirm'})
            self.activity_schedule(
                'mbk_pms.mail_act_pms_contract_approval',
                fields.Datetime.now().date(),
                note="To Approve for contract for " + self.partner_id.name + '\n' + comment,
                user_id=approval_user_id or self.owner_user_id.id or self.env.uid)

    def _add_followers(self):
        for contract in self:
            accounts_user_id = 1107
            partner_ids = (contract.owner_user_id.partner_id).ids
            contract.message_subscribe(partner_ids=partner_ids)

    def action_confirm(self, comment):
        if self.filtered(lambda contract: contract.state == 'confirm'):
            contract_no = self.env['ir.sequence'].next_by_code('mbk_pms.contract')
            self.name = contract_no
            self.write({'state': 'open'})
            self.activity_feedback(['mbk_pms.mail_act_pms_contract_approval'], feedback=comment)
            for line in self.payment_line_ids:
                if line.state == 'draft':
                    line.state = 'active'
            for line in self.unit_line_ids:
                if line.unit_id.is_unit:
                    unit = self.env['mbk_pms.unit'].browse(line.unit_id.id)
                    unit.update({
                        'state': 'occupied',
                        'status': 'occupied',
                        'contract_id': self.id,
                        'customer_id': self.partner_id.id,
                    })
            if self.parent_contract_id:
                self.parent_contract_id.renewed_contract_id = self.id
        else:
            raise UserError("Invalid Status")

    def action_reject(self, comment):
        if self.filtered(lambda contract: contract.state == 'confirm'):
            self.write({'state': 'refuse'})
            self.activity_unlink(['mbk_pms.mail_act_pms_contract_approval'])

    def action_draft(self):
        if self.filtered(lambda contract: contract.state == 'close'):
            raise UserError("Cannot cancel a expired contract.")
        else:
            self.write({'state': 'draft'})

    def action_cancel(self):
        if self.filtered(lambda contract: contract.state == 'close'):
            raise UserError("Cannot cancel a expired contract.")
        else:
            self.write({'state': 'cancel'})
            self.write({'name': 'Cancelled'})
            for line in self.payment_line_ids:
                if line.state in 'draft,active':
                    line.state = 'cancel'
            if self.renewal_offer_id:
                self.renewal_offer_id.state = 'close'

    def action_update_payment_schedule(self):
        if self.net_amount == 0:
            raise UserError("Zero value found. Cannot compute payment schedule.")
        elif not self.payment_terms:
            raise UserError("Payment schedule is missing.")
        elif self.state in ('draft'):
            self.payment_line_ids.unlink()
            start_date = self.start_date
            end_date = self.expiry_date
            delta = relativedelta(end_date, start_date)
            # get months difference
            c_months = (delta.months + (delta.years * 12)) + 1
            c_days = (end_date - start_date).days + 1
            no_of_payment = int(self.payment_terms)
            payment_terms = c_months / no_of_payment
            pt_days = c_days / no_of_payment
            is_mod = False if (c_months % no_of_payment) == 0 else True
            common_chq_amount = 0.00
            common_chq_note = ''
            common_services = ''

            one_time_common_chq_amount = 0.00
            one_time_common_chq_note = ''
            one_time_common_services = ''
            one_time_common_service_id = 0

            common_sd_chq_amount = 0.00
            common_sd_chq_note = ''
            common_sd_services = ''

            # Security Deposit payment if available
            for deposit in self.deposit_line_ids:
                if deposit.is_holding:
                    print("Holding Security Cheque Excluded from computation %s" % (deposit.name))
                else:
                    if deposit.is_separate_chq:
                        self.env['mbk_pms.contract.payment.line'].create({
                            'name': 'Cheque',
                            'note': deposit.name,
                            'contract_id': deposit.contract_id.id,
                            'service_id': deposit.deposit_id.id,
                            'ref_date': start_date,
                            'payment_mode': 'chq',
                            'bank_id': self.bank_id.id,
                            'amount': deposit.amount,
                            'chq_type': deposit.chq_type,
                            'company_id': deposit.company_id.id,
                            'state': 'draft', })
                    else:
                        common_sd_chq_amount += deposit.amount
                        if not common_sd_chq_note:
                            common_sd_chq_note = deposit.name + ": " + str(deposit.amount)
                        else:
                            common_sd_chq_note = common_sd_chq_note + ", " + deposit.name + ": " + str(deposit.amount)
                        if not common_sd_services:
                            common_sd_services = deposit.name
                        else:
                            common_sd_services = common_sd_services + ", " + deposit.name

            if common_sd_chq_amount and common_sd_chq_amount > 0:
                common_sd_service_id = self.env['mbk_pms.service'].search([('name', '=', 'Security Deposit')], limit=1)
                if not common_sd_service_id:
                    common_sd_service_id = self.deposit_line_ids[0].deposit_id
                if self.deposit_line_ids[0].chq_type:
                    chq_type = self.deposit_line_ids[0].chq_type
                else:
                    chq_type = 'dated'

                self.env['mbk_pms.contract.payment.line'].create({
                    'name': 'Cheque',
                    'note': common_sd_services,
                    'contract_id': self.id,
                    'service_id': common_sd_service_id.id,
                    'ref_date': start_date,
                    'payment_mode': 'chq',
                    'bank_id': self.bank_id.id,
                    'amount': common_sd_chq_amount,
                    'chq_type': chq_type,
                    'company_id': self.company_id.id,
                    'state': 'draft', })

            # Service payment if available
            for service in self.service_line_ids:
                if service.is_separate_chq:
                    self.env['mbk_pms.contract.payment.line'].create({
                        'name': 'Cheque',
                        'note': service.name,
                        'contract_id': service.contract_id.id,
                        'service_id': service.service_id.id,
                        'ref_date': start_date,
                        'bank_id': self.bank_id.id,
                        'payment_mode': 'chq',
                        'amount': service.net_amount,
                        'company_id': service.company_id.id,
                        'state': 'draft', })
                elif service.is_one_time:
                    one_time_common_chq_amount += service.net_amount
                    if not one_time_common_chq_note:
                        one_time_common_chq_note = service.name + ": " + str(service.net_amount)
                    else:
                        one_time_common_chq_note = one_time_common_chq_note + ", " + service.name + ": " + str(service.net_amount)
                    if not one_time_common_services:
                        one_time_common_services = service.name
                    else:
                        one_time_common_services = one_time_common_services + ", " + service.name

                else:
                    common_chq_amount = common_chq_amount + service.net_amount
                    if not common_chq_note:
                        common_chq_note = service.name + ": " + str(service.net_amount)
                    else:
                        common_chq_note = common_chq_note + ", " + service.name + ": " + str(service.net_amount)
                    if not common_services:
                        common_services = service.name
                    else:
                        common_services = common_services + ", " + service.name

            # Rent Payment Details
            for unit in self.unit_line_ids:
                common_chq_amount = common_chq_amount + unit.net_rent
                if not common_chq_note:
                    common_chq_note = unit.name + ": " + str(unit.net_rent)
                else:
                    common_chq_note = common_chq_note + ", " + unit.name + ": " + str(unit.net_rent)
                if not common_services:
                    common_services = unit.name
                else:
                    common_services = common_services + ", " + unit.name
            i = 1
            common_chq_allocated = 0.0
            chq_amount = round(common_chq_amount / no_of_payment, 2)
            common_service_id = self.unit_line_ids[0].service_id.id
            note = self.unit_line_ids[0].service_id.name + ': ' + common_services
            self.payment_note = common_chq_note
            ref_date = start_date
            from_date = datetime.combine(start_date, datetime.min.time())
            chq_days = ((chq_amount / common_chq_amount) * c_days) - 1.00
            to_date = from_date + relativedelta(days=chq_days)
            one_time_common_service_id = self.env['mbk_pms.service'].search([('name', '=', 'Services Charges')], limit=1)

            if one_time_common_chq_amount and one_time_common_chq_amount > 0 and not self.is_include_service:
                if not one_time_common_service_id:
                    one_time_common_service_id = self.service_line_ids.filtered(lambda e: e.is_one_time and not e.is_separate_chq)[0]

                self.env['mbk_pms.contract.payment.line'].create({
                    'name': 'Cheque',
                    'note': one_time_common_services,
                    'contract_id': self.id,
                    'service_id': one_time_common_service_id.id,
                    'ref_date': ref_date,
                    'bank_id': self.bank_id.id,
                    'payment_mode': 'chq',
                    'amount': one_time_common_chq_amount,
                    'company_id': self.company_id.id,
                    'state': 'draft', })

            while i <= no_of_payment:
                common_chq_allocated = common_chq_allocated + chq_amount
                if i == no_of_payment:
                    chq_amount = chq_amount + round((common_chq_amount - common_chq_allocated), 2)
                if i > 1:
                    from_date = to_date + relativedelta(days=1)
                    chq_days = ((chq_amount / common_chq_amount) * c_days) - 1.00
                    to_date = from_date + relativedelta(days=chq_days)
                    if is_mod:
                        ref_date = from_date.date()
                    else:
                        ref_date = ref_date + relativedelta(months=payment_terms)
                payment_line_id = self.env['mbk_pms.contract.payment.line'].create({
                    'name': 'Cheque',
                    'note': note,
                    'contract_id': self.id,
                    'service_id': common_service_id,
                    'ref_date': ref_date,
                    'bank_id': self.bank_id.id,
                    'from_date': from_date.date(),
                    'to_date': to_date.date(),
                    'days': chq_days + 1,
                    'payment_mode': 'chq',
                    'amount': chq_amount,
                    'company_id': self.company_id.id,
                    'state': 'draft', })
                if i == 1 and one_time_common_chq_amount and one_time_common_chq_amount > 0 and self.is_include_service:
                    payment_line_id.note += ', '+one_time_common_services
                    payment_line_id.amount += one_time_common_chq_amount
                i = i + 1
        else:
            raise UserError("Draft Payment schedule can only re-computed.")
        return

    def action_done_update_state_wizard(self):
        approval_user_id = self.env['ir.config_parameter'].get_param('mbk_pms_lease_offer_approver_id')
        total_payment = 0
        held_deposit = 0.00
        for line in self.payment_line_ids:
            total_payment += line.amount

        for deposit in self.deposit_line_ids:
            if deposit.is_holding:
                held_deposit += deposit.amount

        if round(total_payment, 2) != round((self.net_amount-held_deposit), 2):
            print(total_payment, self.net_amount, held_deposit)
            raise UserError("Payment schedule not matching with Net Contract amount")

        return {
            'name': 'Update Status',
            'res_model': 'mbk_pms.update_state_wizard',
            'view_mode': 'form',
            'context': {'default_doc_id': self.id, 'default_status': 'done', 'default_label_name': 'Submit for Approval'},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_confirm_update_state_wizard(self):
        return {
            'name': 'Update Status',
            'res_model': 'mbk_pms.update_state_wizard',
            'view_mode': 'form',
            'context': {'default_doc_id': self.id, 'default_status': 'confirm', 'default_label_name': 'Approve'},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_cancel_update_state_wizard(self):
        return {
            'name': 'Update Status',
            'res_model': 'mbk_pms.update_state_wizard',
            'view_mode': 'form',
            'context': {'default_doc_id': self.id, 'default_status': 'cancel', 'default_label_name': 'Cancel'},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_reject_update_state_wizard(self):
        return {
            'name': 'Update Status',
            'res_model': 'mbk_pms.update_state_wizard',
            'view_mode': 'form',
            'context': {'default_doc_id': self.id, 'default_status': 'refuse', 'default_label_name': 'Reject'},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_create_payment_collection(self):
        if not self.payment_line_ids:
            raise UserError("Payment schedule not exits")
        if not self.receipt_id:
            payment_id = self.env['mbk_pms.payment_collection'].create(
                {'contract_id': self.id,
                 'note': 'Payment collection against contract ' + self.name + ' Unit: ' + self.unit_id.name,
                 'unit_id': self.unit_id.id,
                 'property_id': self.property_id.id, 'tenant_id': self.partner_id.id, })
            for line in self.payment_line_ids:
                self.env['mbk_pms.payment_collection.line'].create(
                    {'service_id': line.service_id.id, 'receipt_id': payment_id.id, 'name': line.note,
                     'payment_line_id': line.id, 'payment_mode': line.payment_mode, 'ref_date': line.ref_date, 'ref_no': line.ref_no, 'bank_id': line.bank_id.id,
                     'amount': line.amount, 'contract_id': line.contract_id, })
            self.receipt_id = payment_id.id
            return {
                'name': 'Payment Collection',
                'res_model': 'mbk_pms.payment_collection',
                'view_mode': 'form',
                'res_id': payment_id.id,
                'context': {'default_contract_id': self.id},
                'domain': [('contract_id', '=', self.id), ],
                'target': 'current',
                'type': 'ir.actions.act_window',
            }
        else:
            raise UserError("Payment collection voucher already exits")


class PMSContractUnitLines(models.Model):
    _name = 'mbk_pms.contract.unit.line'
    _description = 'Unit Details'

    contract_id = fields.Many2one('mbk_pms.contract', string='Contract Reference', required=True, ondelete='cascade',
                                  index=True, copy=False)
    unit_id = fields.Many2one('mbk_pms.unit', string='Unit', domain="[('state', '=', 'available')]")
    service_id = fields.Many2one('mbk_pms.service', string='Services', required=True,
                                 domain="[('category', '=', 'rent')]")
    name = fields.Char(string='Unit Details', required=True)
    unit_type_id = fields.Many2one(related='unit_id.type_id', string='Type')
    property_id = fields.Many2one(related='unit_id.property_id', string='Property')
    last_year_rent = fields.Float(string="Last year rent", default=0, readonly=True)
    original_rent = fields.Float(string="Rent", default=0)
    discount = fields.Float(string="Discount", default=0)
    agreement_rent = fields.Float(string="Agreement Rent", default=0)
    is_tax = fields.Boolean(string="Tax")
    tax_id = fields.Many2one('account.tax', string='Taxes', domain="[('type_tax_use', '=', 'sale')]")
    tax_amount = fields.Float(string="Tax Amount", default=0)
    net_rent = fields.Float(string="Net Rent", default=0)
    company_id = fields.Many2one(related='contract_id.company_id', string='Company')
    state = fields.Selection(
        related='contract_id.state', string='Contract Status', copy=False, store=True)
    start_date = fields.Date(related='contract_id.start_date', string='Start Date', help="Contract Valid from date.",
                             copy=False)
    expiry_date = fields.Date(related='contract_id.expiry_date', string='Expiration Date', help="Contract Valid upto.",
                              copy=False)

    @api.onchange('unit_id')
    def onchange_unit_id(self):
        if self.unit_id.use_type == 'com':
            self.is_tax = True
            service_id = self.env['mbk_pms.service'].search([('name', '=', 'Commercial Rent')], limit=1)
            self.service_id = service_id
        else:
            self.is_tax = False
            service_id = self.env['mbk_pms.service'].search([('name', '=', 'Residential Rent')], limit=1)
            self.service_id = service_id
        if self.unit_id:
            self.name = self.unit_id.name
            if self.unit_id.rent:
                self.original_rent = self.unit_id.rent
            else:
                self.original_rent = 0.00

    @api.onchange('original_rent', 'discount')
    def onchange_rent(self):
        self.agreement_rent = self.original_rent - self.discount

    @api.onchange('is_tax')
    def onchange_is_tax(self):
        if self.is_tax and self.property_id:
            if self.property_id.state_id and self.property_id.state_id.code == 'AZ':
                self.tax_id = self.env['account.tax'].search([('name', '=', 'VAT 5% (Abu Dhabi)')], limit=1)
            elif self.property_id.state_id and self.property_id.state_id.code == 'DU':
                self.tax_id = self.env['account.tax'].search([('name', '=', 'VAT 5% (Dubai)')], limit=1)
            elif self.property_id.state_id and self.property_id.state_id.code == 'SH':
                self.tax_id = self.env['account.tax'].search([('name', '=', 'VAT 5% (Sharjah)')], limit=1)
            elif self.property_id.state_id and self.property_id.state_id.code == 'AJ':
                self.tax_id = self.env['account.tax'].search([('name', '=', 'VAT 5% (Ajman)')], limit=1)
            elif self.property_id.state_id and self.property_id.state_id.code == 'UQ':
                self.tax_id = self.env['account.tax'].search([('name', '=', 'VAT 5% (Umm Al Quwain)')], limit=1)
            elif self.property_id.state_id and self.property_id.state_id.code == 'RK':
                self.tax_id = self.env['account.tax'].search([('name', '=', 'VAT 5% (Ras Al-Khaima)')], limit=1)
            elif self.property_id.state_id and self.property_id.state_id.code == 'FU':
                self.tax_id = self.env['account.tax'].search([('name', '=', 'VAT 5% (Fujairah)')], limit=1)
            else:
                self.tax_id = self.tax_id = self.env['account.tax'].search([('name', '=', 'VAT 5% (Abu Dhabi)')], limit=1)
            service_id = self.env['mbk_pms.service'].search([('name', '=', 'Commercial Rent')], limit=1)
            self.service_id = service_id
        else:
            self.tax_id = False
            service_id = self.env['mbk_pms.service'].search([('name', '=', 'Residential Rent')], limit=1)
            self.service_id = service_id

    @api.onchange('agreement_rent', 'tax_id')
    def onchange_tax(self):
        if self.is_tax and self.tax_id:
            self.tax_amount = (self.agreement_rent * self.tax_id.amount) / 100
        else:
            self.tax_amount = 0.0
        self.net_rent = self.agreement_rent + self.tax_amount


class PMSContractServiceLines(models.Model):
    _name = 'mbk_pms.contract.service.line'
    _description = 'Service Details'

    contract_id = fields.Many2one('mbk_pms.contract', string='Contract Reference', required=True, ondelete='cascade',
                                  index=True, copy=False)
    service_id = fields.Many2one('mbk_pms.service', string='Services', required=True,
                                 domain="[('category', '=', 'service')]")
    name = fields.Char(string='Service Details', required=True)
    amount = fields.Float(string="Amount", default=0)
    is_tax = fields.Boolean(string="Tax", default=True)
    tax_id = fields.Many2one('account.tax', string='Taxes', domain="[('type_tax_use', '=', 'sale')]")
    tax_amount = fields.Float(string="Tax Amount", default=0)
    net_amount = fields.Float(string="Net Amount", default=0)
    is_separate_chq = fields.Boolean(string="Separate Cheque")
    is_one_time = fields.Boolean(string="One Time")
    company_id = fields.Many2one(related='contract_id.company_id', string='Company')

    @api.onchange('service_id')
    def onchange_service_id(self):
        if self.service_id:
            self.is_tax = self.service_id.is_tax
            self.is_one_time = self.service_id.is_one_time
            self.is_separate_chq = self.service_id.is_separate_chq
            self.name = self.service_id.name
        else:
            self.is_tax = False
        if self.service_id.price:
            self.amount = self.service_id.price
        else:
            self.amount = 0.0

    @api.onchange('amount', 'tax_id')
    def onchange_tax(self):
        if self.is_tax and self.tax_id:
            self.tax_amount = (self.amount * self.tax_id.amount) / 100
        else:
            self.tax_amount = 0.0
        self.net_amount = self.amount + self.tax_amount

    @api.onchange('is_tax')
    def onchange_is_tax(self):

        if self.contract_id.unit_line_ids[0].property_id.state_id:
            state_id = self.contract_id.unit_line_ids[0].property_id.state_id
        elif self.contract_id.state_id:
            state_id = self.contract_id.unit_line_ids[0].property_id.state_id
        else:
            state_id = False

        if self.is_tax and state_id:
            if state_id and state_id.code == 'AZ':
                self.tax_id = self.env['account.tax'].search([('name', '=', 'VAT 5% (Abu Dhabi)')], limit=1)
            elif state_id and state_id.code == 'DU':
                self.tax_id = self.env['account.tax'].search([('name', '=', 'VAT 5% (Dubai)')], limit=1)
            elif state_id and state_id.code == 'SH':
                self.tax_id = self.env['account.tax'].search([('name', '=', 'VAT 5% (Sharjah)')], limit=1)
            elif state_id and state_id.code == 'AJ':
                self.tax_id = self.env['account.tax'].search([('name', '=', 'VAT 5% (Ajman)')], limit=1)
            elif state_id and state_id.code == 'UQ':
                self.tax_id = self.env['account.tax'].search([('name', '=', 'VAT 5% (Umm Al Quwain)')], limit=1)
            elif state_id and state_id.code == 'RK':
                self.tax_id = self.env['account.tax'].search([('name', '=', 'VAT 5% (Ras Al-Khaima)')], limit=1)
            elif state_id and state_id.code == 'FU':
                self.tax_id = self.env['account.tax'].search([('name', '=', 'VAT 5% (Fujairah)')], limit=1)
            else:
                self.tax_id = self.env['account.tax'].search([('name', '=', 'VAT 5% (Abu Dhabi)')], limit=1)
        else:
            self.tax_id = False


class PMSContractDepositLines(models.Model):
    _name = 'mbk_pms.contract.deposit.line'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'Security Deposit Details'

    contract_id = fields.Many2one('mbk_pms.contract', string='Contract Reference', required=True, ondelete='cascade',
                                  index=True, copy=False)
    deposit_id = fields.Many2one('mbk_pms.service', string='Deposit Type', required=True,
                                 domain="[('category', '=', 'deposit')]")
    name = fields.Char(string='Description', required=True)
    amount = fields.Float(string="Amount", default=0)
    chq_type = fields.Selection([('blank', 'Blank Dated Cheque'), ('dated', 'Dated Cheque'), ], string='Cheque Type',
                                copy=False, default='blank', help="""Cheque Type""")
    company_id = fields.Many2one(related='contract_id.company_id', string='Company')
    is_separate_chq = fields.Boolean(string="Separate Cheque")
    is_holding = fields.Boolean(string="Holding", readonly=True, default=False)
    start_date = fields.Date(related='contract_id.start_date', string='Start Date', help="Contract Valid from date.",
                             copy=False)
    expiry_date = fields.Date(related='contract_id.expiry_date', string='Expiration Date', help="Contract Valid upto.",
                              copy=False)
    state = fields.Selection([('draft', 'Draft'), ('active', 'Active'), ('paid', 'Paid'), ('cancel', 'Cancelled'), ('received', 'Received'),
                              ('deposited', 'Deposited'), ('cleared', 'Cleared'), ('forwarded', 'Forwarded'), ], string='Status', index=True, readonly=True, copy=False,
                             tracking=True, default='draft', help="""Status of Security Deposit""")
    received_date = fields.Date(string='Received Date', copy=False, readonly=True)
    settled_date = fields.Date(string='Settled Date', copy=False, readonly=True)

    @api.onchange('deposit_id')
    def onchange_deposit_id(self):
        if self.deposit_id:
            self.is_separate_chq = self.deposit_id.is_separate_chq
            if not self.name:
                self.name = self.deposit_id.description


class PMSContractPaymentSchedule(models.Model):
    _name = 'mbk_pms.contract.payment.line'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'Payment Schedule Details'

    contract_id = fields.Many2one('mbk_pms.contract', string='Contract Reference', required=True, ondelete='cascade',
                                  index=True, copy=False)
    service_id = fields.Many2one('mbk_pms.service', string='Service', required=True, domain="[('category', '=', 'service')]")
    name = fields.Char(string='Description', copy=False)
    note = fields.Text(string='Remarks', copy=False)
    ref_date = fields.Date(string='Date', copy=False)
    payment_mode = fields.Selection(
        [('chq', 'Cheque'), ('cash', 'Cash'), ('transfer', 'Transfer'), ('credit', 'Credit')], string='Payment Mode',
        copy=False, default='chq')
    ref_no = fields.Char(string='Cheque/Ref No', copy=False)
    bank_id = fields.Many2one('res.bank', string='Bank', copy=False)
    amount = fields.Float(string="Amount", default=0)
    chq_type = fields.Selection([('blank', 'Blank Dated Cheque'), ('dated', 'Dated Cheque'), ], string='Cheque Type',
                                copy=False, help="""Cheque Type""")
    from_date = fields.Date(string='From Date', copy=False)
    to_date = fields.Date(string='To Date', copy=False)
    days = fields.Float(string='Days', copy=False)
    company_id = fields.Many2one(related='contract_id.company_id', string='Company')
    tenant_id = fields.Many2one(related='contract_id.partner_id', string='Tenant')
    unit_id = fields.Many2one(related='contract_id.unit_id', string='Unit', copy=False, store=True)
    property_id = fields.Many2one(related='contract_id.property_id', string='Property', copy=False, store=True)
    state_id = fields.Many2one(related='contract_id.property_id.state_id', string='Emirate', copy=False, store=True)
    depositing_bank_id = fields.Many2one('account.journal', string='Account', domain="[('type', 'in', ('bank','cash'))]",
                                         tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('active', 'Active'), ('received', 'Received'), ('hold', 'Hold'),
                              ('deposited', 'Deposited'), ('cleared', 'Cleared'), ('bounced', 'Bounced'),
                              ('replaced', 'Replaced'), ('legal', 'Legal'),
                              ('cancel', 'Cancelled'), ], string='Status', index=True, readonly=True, copy=False,
                             tracking=True, default='draft', help="""Status of cheque""")
    last_activity_date = fields.Date(string='Last Activity Date', copy=False, readonly=True)
    received_date = fields.Date(string='Received Date', copy=False, readonly=True)
    deposited_date = fields.Date(string='Deposited Date', copy=False, readonly=True)
    parent_id = fields.Many2one('mbk_pms.contract.payment.line', string='Parent Reference', readonly=True)
    reference_id = fields.Char(string="Reference ID")
    category = fields.Selection([('main', 'Main'), ('other', 'Others')], string='Category', copy=False, default='main')

    @api.onchange('service_id')
    def onchange_service_id(self):
        if not self.note:
            self.note = self.service_id.description

    @api.onchange('payment_mode', 'ref_no', 'bank_id')
    def onchange_payment_mode(self):
        if self.payment_mode:
            if self.payment_mode in ('cash', 'credit'):
                self.bank_id = False
                self.depositing_bank_id = False
            elif self.payment_mode in ('chq', 'transfer'):
                if self.contract_id.bank_id:
                    self.bank_id = self.contract_id.bank

        pm = self._fields['payment_mode'].selection
        pm_dict = dict(pm)
        payment_mode = pm_dict.get(self.payment_mode)
        name = ''

        if self.ref_no and self.payment_mode == 'chq':
            if not self.ref_no.isnumeric():
                self.ref_no = False
                raise UserError("Please enter valid numeric cheque number")
            if len(self.ref_no) != 6:
                self.ref_no = self.ref_no.zfill(6)

        if self.contract_id.name != 'Draft':
            name += self.contract_id.name
        if self.bank_id:
            if name:
                name += '-'
            name += self.bank_id.name
        if name:
            name += '-'
        name += payment_mode
        if self.ref_no:
            if name:
                name += '-'
            name += self.ref_no
        self.name = name
