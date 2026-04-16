# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class PmsLeaseOffer(models.Model):
    _name = 'mbk_pms.lease_offer'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'Lease Offer'

    name = fields.Char(string='Offer No', tracking=True, default='Draft', copy=False, readonly=True)
    revision_no = fields.Integer(string='Revisions', tracking=True, copy=False, readonly=True)
    enquiry_date = fields.Date(string='Enquiry Date', default=fields.Date.context_today, copy=False)
    enquiry_summary = fields.Char(string='Enquiry Summary', copy=False)
    partner_id = fields.Many2one(
        'res.partner', string='Tenant', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        required=True, change_default=True, index=True, tracking=1,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", )
    partner_contact_id = fields.Many2one(related='partner_id', string='Tenant Address')
    offer_date = fields.Date(string='Offer Date', copy=False, tracking=True)
    state = fields.Selection([
        ('draft', 'Enquiry'),
        ('confirm', 'To Approve'),
        ('active', 'Lease Offer'),
        ('sent', 'Approved'),
        ('done', 'Confirmed'),
        ('refuse', 'Rejected'),
        ('close', 'Expired'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, copy=False, tracking=True, default='draft',
        help="""Status of the Lease Enquiry""")
    required_date = fields.Date(string='Required Date', help="Unit ", copy=False, required=True)
    start_date = fields.Date(string='Start Date', help="Contract Valid from date.", copy=False)
    expiry_date = fields.Date(string='Expiration Date', help="Contract Valid upto.", copy=False)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, copy=False)
    state_id = fields.Many2one('res.country.state', string='Emirate', domain="[('country_id', '=', 2)]")
    property_type_id = fields.Many2one('mbk_pms.property_type', string='Property Type')
    property_id = fields.Many2one('mbk_pms.property', string='Property')
    unit_type_id = fields.Many2one('mbk_pms.unit_type', string='Unit Type')
    sq_ft_min = fields.Float(string='Sqr Ft Min')
    sq_ft_max = fields.Float(string='Sqr Ft Max')
    beds_min = fields.Integer(string='Beds Min')
    beds_max = fields.Integer(string='Beds Max')
    bath_min = fields.Integer(string='Bath Min')
    bath_max = fields.Integer(string='Bath Max')
    vacant_unit_ids = fields.Many2many('mbk_pms.unit', 'mbk_pms_offer_vacant_unit_rel', string='Vacant Units', domain="[('state', '=', 'available')]")
    vacant_count = fields.Integer(string='Vacant Units Count', default=False, readonly=True)
    unit_id = fields.Many2one('mbk_pms.unit', string='Unit', copy=False, domain="[('id', 'in', vacant_unit_ids)]")
    is_tax = fields.Boolean(string="Tax")
    is_include_service = fields.Boolean(string="Service charges with first payment", default=False)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id,
                                  store=True)
    owner_user_id = fields.Many2one('res.users', string='Sales Person', default=lambda s: s.env.uid, copy=False)
    valid_upto = fields.Date(string='Valid Upto', help="Offer Valid upto.", copy=False)
    mobile = fields.Char(related='partner_id.mobile', string='Mobile No', copy=False, store=True)
    email = fields.Char(related='partner_id.email', string='Email', copy=False, store=True)

    payment_terms = fields.Selection(
        [('1', '1 Times'), ('2', '2 Times'), ('3', '3 Times'), ('4', '4 Times'), ('5', '5 Times'),
         ('6', '6 Times'), ('7', '7 Times'), ('8', '8 Times'), ('9', '9 Times'), ('10', '10 Times'), ('11', '11 Times'),
         ('12', '12 Times'), ], string='Payment Terms', copy=False, tracking=True, default='4',
        help="""Status of the Renewal Offer""")
    note = fields.Text(string='Notes', copy=False)
    payment_note = fields.Text(string='Payment Notes', copy=False)
    active = fields.Boolean(string="Active", default=True, tracking=True, copy=False)
    units = fields.Char(string='Units', copy=False, store=True, readonly=True, compute='_compute_net_rent')
    unit_line_ids = fields.One2many('mbk_pms.lease_offer.unit.line', 'lease_offer_id', string='Unit Lines',
                                    readonly=True,
                                    states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
                                    copy=False, auto_join=True)
    service_line_ids = fields.One2many('mbk_pms.lease_offer.service.line', 'lease_offer_id', string='Service Lines',
                                       states={'cancel': [('readonly', True)], 'close': [('readonly', True)]},
                                       copy=False, auto_join=True)
    deposit_line_ids = fields.One2many('mbk_pms.lease_offer.deposit.line', 'lease_offer_id', string='Deposit Lines',
                                       states={'cancel': [('readonly', True)], 'close': [('readonly', True)]},
                                       copy=False, auto_join=True)
    payment_line_ids = fields.One2many('mbk_pms.lease_offer.payment.line', 'lease_offer_id',
                                       string='Payment Schedule Lines',
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
    contract_id = fields.Many2one('mbk_pms.contract', string='Contract ID', copy=False, readonly='True')

    @api.onchange('offer_date')
    def onchange_offer_date(self):
        if self.offer_date:
            self.valid_upto = self.offer_date + relativedelta(days=15)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.partner_contact_id = self.partner_id
            if self.partner_id.state_id:
                self.state_id = self.partner_id.state_id
        else:
            self.partner_contact_id = False

    @api.onchange('required_date')
    def onchange_required_date(self):
        if self.required_date:
            self.start_date = self.required_date

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

    @api.onchange('unit_id')
    def onchange_unit_id(self):
        if self.unit_id.use_type == 'com':
            self.is_tax = True
        else:
            self.is_tax = False

    @api.depends('unit_line_ids')
    def _compute_net_rent(self):
        for offer in self:
            total_rent = 0.00
            total_rent_tax = 0.00
            net_rent_amount = 0.00
            units = ''

            for line in offer.unit_line_ids:
                total_rent += line.agreement_rent
                total_rent_tax += line.tax_amount
                net_rent_amount += line.net_rent
                if units == '':
                    units = line.unit_id.name
                else:
                    units = units + ', ' + line.unit_id.name
                if not self.unit_id:
                    self.unit_id = line.unit_id.id

            offer.update({
                'total_rent': total_rent,
                'total_rent_tax': total_rent_tax,
                'net_rent_amount': net_rent_amount,
                'units': units,
            })

    @api.depends('service_line_ids')
    def _compute_net_service(self):
        for offer in self:
            total_service = 0.00
            total_service_tax = 0.00
            net_service_amount = 0.00

            for line in offer.service_line_ids:
                total_service += line.amount
                total_service_tax += line.tax_amount
                net_service_amount += line.net_amount

            offer.update({
                'total_service': total_service,
                'total_service_tax': total_service_tax,
                'net_service_amount': net_service_amount,
            })

    @api.depends('deposit_line_ids')
    def _compute_net_deposit(self):
        for offer in self:
            total_deposit = 0.00

            for line in offer.deposit_line_ids:
                total_deposit += line.amount

            offer.update({
                'total_deposit': total_deposit,
            })

    @api.model
    def create(self, vals):
        # context: no_log, because subtype already handle this
        offer = super(PmsLeaseOffer, self).create(vals)
        return offer

    def name_get(self):
        return [(rec.id, "%s" % (rec.enquiry_summary if rec.state == 'draft' else rec.name)) for rec in self]

    def action_done(self, comment):
        approval_user_id = self.env['ir.config_parameter'].get_param('mbk_pms_lease_offer_approver_id')

        if self.filtered(lambda offer: offer.state == 'active'):
            if self.name == 'Draft':
                offer_no = self.env['ir.sequence'].next_by_code('mbk_pms.lease_offer')
                self.name = offer_no
                self.revision_no = 0
            else:
                self.revision_no += 1

            self.offer_date = date.today()
            self.write({'state': 'confirm'})
            self.activity_schedule(
                'mbk_pms.mail_act_pms_lease_offer_approval',
                fields.Datetime.now().date(),
                note="To Approve for offer for " + self.name + ' ' + self.partner_id.name + '\n' + comment,
                user_id=approval_user_id or self.owner_user_id.id or self.env.uid)

    def _add_followers(self):
        for offer in self:
            accounts_user_id = 1107
            partner_ids = (offer.owner_user_id.partner_id).ids
            offer.message_subscribe(partner_ids=partner_ids)

    def action_confirm(self, comment):
        if self.filtered(lambda offer: offer.state == 'confirm'):
            self.write({'state': 'sent'})
            self.activity_feedback(['mbk_pms.mail_act_pms_lease_offer_approval'], feedback=comment)
        else:
            raise UserError("Invalid Status")

    def action_reject(self, comment):
        if self.filtered(lambda offer: offer.state == 'confirm'):
            self.write({'state': 'refuse'})
            self.activity_unlink(['mbk_pms.mail_act_pms_lease_offer_approval'])

    def action_draft(self):
        if self.filtered(lambda offer: offer.state == 'close'):
            raise UserError("Cannot cancel a expired Offer letter.")
        else:
            self.write({'state': 'active'})

    def action_cancel(self):
        if self.filtered(lambda offer: offer.state == 'close'):
            raise UserError("Cannot cancel a expired renewal offer.")
        else:
            self.write({'state': 'cancel'})
            self.write({'name': 'Cancelled'})
            for line in self.payment_line_ids:
                if line.state in 'draft,active':
                    line.state = 'cancel'

    def action_update_payment_schedule(self):
        if self.net_amount == 0 or self.net_rent_amount == 0:
            raise UserError("Zero value found. Cannot compute payment schedule.")
        elif not self.payment_terms:
            raise UserError("Payment schedule is missing.")
        elif self.state in ('draft', 'active'):
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
                if deposit.is_separate_chq:
                    self.env['mbk_pms.lease_offer.payment.line'].create({
                        'name': deposit.name,
                        'note': '',
                        'lease_offer_id': deposit.lease_offer_id.id,
                        'service_id': deposit.deposit_id.id,
                        'ref_date': start_date,
                        'amount': deposit.amount,
                        'company_id': deposit.company_id.id, })
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

                self.env['mbk_pms.lease_offer.payment.line'].create({
                    'name': common_sd_services,
                    'note': '',
                    'lease_offer_id': self.id,
                    'service_id': common_sd_service_id.id,
                    'ref_date': start_date,
                    'amount': common_sd_chq_amount,
                    'chq_type': chq_type,
                    'company_id': self.company_id.id, })

            # Service payment if available
            for service in self.service_line_ids:
                if service.is_separate_chq:
                    self.env['mbk_pms.lease_offer.payment.line'].create({
                        'name': service.name,
                        'note': '',
                        'lease_offer_id': service.lease_offer_id.id,
                        'service_id': service.service_id.id,
                        'ref_date': start_date,
                        'amount': service.net_amount,
                        'company_id': service.company_id.id, })
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
                self.env['mbk_pms.lease_offer.payment.line'].create({
                    'name': one_time_common_services,
                    'note': '',
                    'lease_offer_id': self.id,
                    'service_id': one_time_common_service_id.id,
                    'ref_date': ref_date,
                    'amount': one_time_common_chq_amount,
                    'company_id': self.company_id.id, })

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

                payment_line_id = self.env['mbk_pms.lease_offer.payment.line'].create({
                    'name': note,
                    'note': '',
                    'lease_offer_id': self.id,
                    'service_id': common_service_id,
                    'ref_date': ref_date,
                    'from_date': from_date.date(),
                    'to_date': to_date.date(),
                    'days': chq_days + 1,
                    'amount': chq_amount,
                    'company_id': self.company_id.id, })
                if i == 1 and one_time_common_chq_amount and one_time_common_chq_amount > 0 and self.is_include_service:
                    payment_line_id.name += ', '+one_time_common_services
                    payment_line_id.amount += one_time_common_chq_amount
                i = i + 1
        else:
            raise UserError("Draft/Lease Offer status payment schedule can only re-computed.")
        return

    def action_done_update_state_wizard(self):
        approval_user_id = self.env['ir.config_parameter'].get_param('mbk_pms_lease_offer_approver_id')
        total_payment = 0

        for line in self.payment_line_ids:
            total_payment += line.amount

        if round(total_payment, 2) != round(self.net_amount, 2):
            raise UserError("Payment schedule not matching with Net Renewal Offer amount")
        return {
            'name': 'Update Status',
            'res_model': 'mbk_pms.update_state_wizard',
            'view_mode': 'form',
            'context': {'default_doc_id': self.id, 'default_status': 'done',
                        'default_label_name': 'Submit for Approval', 'default_model_name': 'lease_offer'},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_confirm_update_state_wizard(self):
        return {
            'name': 'Update Status',
            'res_model': 'mbk_pms.update_state_wizard',
            'view_mode': 'form',
            'context': {'default_doc_id': self.id, 'default_status': 'confirm', 'default_label_name': 'Approve',
                        'default_model_name': 'lease_offer'},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_cancel_update_state_wizard(self):
        return {
            'name': 'Update Status',
            'res_model': 'mbk_pms.update_state_wizard',
            'view_mode': 'form',
            'context': {'default_doc_id': self.id, 'default_status': 'cancel', 'default_label_name': 'Cancel',
                        'default_model_name': 'lease_offer'},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_reject_update_state_wizard(self):
        return {
            'name': 'Update Status',
            'res_model': 'mbk_pms.update_state_wizard',
            'view_mode': 'form',
            'context': {'default_doc_id': self.id, 'default_status': 'refuse', 'default_label_name': 'Reject',
                        'default_model_name': 'lease_offer'},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_search_units(self):
        if self.state in ('draft'):
            # self.bounced_line_ids.unlink()
            unit_filter = [('state', '=', 'available')]
            if self.state_id:
                unit_filter.append(('property_id.state_id', '=', self.state_id.id))
            if self.property_type_id:
                unit_filter.append(('property_id.property_type_id', '=', self.property_id.id))
            if self.property_id:
                unit_filter.append(('property_id', '=', self.property_id.id))
            if self.unit_type_id:
                unit_filter.append(('type_id', '=', self.unit_type_id.id))
            if self.sq_ft_min and self.sq_ft_min != 0:
                unit_filter.append(('sq_ft', '>=', self.sq_ft_min))
            if self.sq_ft_max and self.sq_ft_max != 0:
                unit_filter.append(('sq_ft', '<=', self.sq_ft_max))
            if self.beds_min and self.beds_min != 0:
                unit_filter.append(('no_of_beds', '>=', self.beds_min))
            if self.beds_max and self.beds_max != 0:
                unit_filter.append(('no_of_beds', '<=', self.beds_max))
            if self.bath_min and self.bath_min != 0:
                unit_filter.append(('no_of_baths', '>=', self.bath_min))
            if self.bath_max and self.bath_max != 0:
                unit_filter.append(('no_of_baths', '<=', self.bath_max))
            if self.start_date:
                from_date = self.start_date
            else:
                from_date = date.today()
            unit_filter.append('|')
            unit_filter.append(('available_from_date', '=', False))
            unit_filter.append(('available_from_date', '<=', from_date))
            self.vacant_unit_ids = self.env['mbk_pms.unit'].search(unit_filter)
            self.vacant_count = len(self.vacant_unit_ids)
            # print("Unit Filter", unit_filter)
        return

    def action_reset_search(self):
        self.vacant_unit_ids = False
        if self.start_date:
            from_date = self.start_date
        else:
            from_date = date.today()
        self.vacant_unit_ids = self.env['mbk_pms.unit'].search([('state', '=', 'available'), '|', ('available_from_date', '=', False), ('available_from_date', '<=', from_date)])
        self.vacant_count = len(self.vacant_unit_ids)
        return

    def action_lease_offer(self):
        if self.unit_id and self.state == 'draft':
            if self.unit_line_ids:
                self.unit_line_ids.unlink()
            if self.service_line_ids:
                self.service_line_ids.unlink()
            if self.deposit_line_ids:
                self.deposit_line_ids.unlink()
            if self.unit_id.use_type == 'com':
                is_tax = True
                service_id = self.env['mbk_pms.service'].search([('name', '=', 'Commercial Rent')], limit=1)
            else:
                is_tax = False
                service_id = self.env['mbk_pms.service'].search([('name', '=', 'Residential Rent')], limit=1)
            print(self.unit_id.name)

            unit_line = self.env['mbk_pms.lease_offer.unit.line'].create({'lease_offer_id': self.id, 'unit_id': self.unit_id.id,
                                                                          'service_id': service_id.id, 'is_tax': is_tax, 'name': self.unit_id.name})
            unit_line.onchange_unit_id()
            unit_line.onchange_rent()
            unit_line.onchange_is_tax()
            unit_line.onchange_tax()
            # Load service details
            if self.unit_id.property_id.state_id.name == 'Abu Dhabi':
                contract_fee = 'Tawtheeq Fee'
            else:
                contract_fee = 'Ejari Fee'
            service_ids = self.env['mbk_pms.service'].search([('name', 'in', (contract_fee, 'New Contract Fee', 'Leasing Fee')), ('category', '=', 'service')])
            for service in service_ids:
                service_line = self.env['mbk_pms.lease_offer.service.line'].create(
                        {'lease_offer_id': self.id, 'service_id': service.id, 'name': service.name, })
                service_line.onchange_service_id()
                service_line.onchange_is_tax()
                service_line.onchange_tax()

            # Load deposit details
            deposit_id = self.env['mbk_pms.service'].search([('name', '=', 'Security Deposit'), ('category', '=', 'deposit')], limit=1)
            deposit_amount = 0
            if self.total_rent:
                if deposit_id.price:
                    deposit_amount = round((deposit_id.price * self.total_rent)/100, -2)

            deposit_line = self.env['mbk_pms.lease_offer.deposit.line'].create(
                        {'lease_offer_id': self.id, 'deposit_id': deposit_id.id, 'name': deposit_id.name,
                         'amount': deposit_amount, 'chq_type': 'dated', 'is_separate_chq': deposit_id.is_separate_chq, })
            self.onchange_net_tax()
            self.onchange_net_amount()
            if self.net_rent_amount:
                self.action_update_payment_schedule()
            self.write({'state': 'active'})
        else:
            raise UserError("Please select the unit for creating lease offer.")
        return

    def action_update_units(self):
        if self.unit_id and self.state == 'active':
            if self.unit_line_ids:
                self.unit_line_ids.unlink()
            if self.payment_line_ids:
                self.payment_line_ids.unlink()

            if self.unit_id.use_type == 'com':
                is_tax = True
                service_id = self.env['mbk_pms.service'].search([('name', '=', 'Commercial Rent')], limit=1)
            else:
                is_tax = False
                service_id = self.env['mbk_pms.service'].search([('name', '=', 'Residential Rent')], limit=1)

            unit_line = self.env['mbk_pms.lease_offer.unit.line'].create({'lease_offer_id': self.id, 'unit_id': self.unit_id.id,
                                                                          'service_id': service_id.id, 'is_tax': is_tax, 'name': self.unit_id.name})
            unit_line.onchange_unit_id()
            unit_line.onchange_rent()
            unit_line.onchange_is_tax()
            unit_line.onchange_tax()

    def action_create_contract(self):
        if self.contract_id:
            raise ValidationError("Related contract is already available %s." % (self.contract_id.name))
        else:
            # Create contract from lease offer
            contract_id = self.env['mbk_pms.contract'].create(
                {'lease_offer_id': self.id,
                 'partner_id': self.partner_id.id,
                 'start_date': self.start_date, 'expiry_date': self.expiry_date,
                 'unit_id': self.unit_id.id, 'property_id': self.property_id.id,
                 'state_id': self.state_id.id,
                 'payment_terms': self.payment_terms,
                 'units': self.units, 'net_amount': self.net_amount,
                 })
            # Create Unit Lines
            for unit in self.unit_line_ids:
                unit_line = self.env['mbk_pms.contract.unit.line'].create(
                    {'contract_id': contract_id.id, 'unit_id': unit.unit_id.id, 'service_id': unit.service_id.id,
                     'name': unit.name, 'original_rent': unit.original_rent,
                     'discount': unit.discount, 'agreement_rent': unit.agreement_rent, 'tax_amount': unit.tax_amount, 'net_rent': unit.net_rent,
                     'is_tax': unit.is_tax, 'tax_id': unit.tax_id.id, })

            # Load service details
            for service in self.service_line_ids:
                service_line = self.env['mbk_pms.contract.service.line'].create(
                    {'contract_id': contract_id.id, 'service_id': service.service_id.id, 'name': service.name,
                     'amount': service.amount, 'is_tax': service.is_tax, 'tax_id': service.tax_id.id,
                     'tax_amount': service.tax_amount, 'net_amount': service.net_amount,
                     'is_separate_chq': service.is_separate_chq, 'is_one_time': service.is_one_time, })

            # Load deposit details
            for deposit in self.deposit_line_ids:
                self.env['mbk_pms.contract.deposit.line'].create(
                    {'contract_id': contract_id.id, 'deposit_id': deposit.deposit_id.id, 'name': deposit.name,
                     'amount': deposit.amount, 'chq_type': deposit.chq_type,
                     'is_separate_chq': deposit.is_separate_chq, 'state': 'draft', })

            # Load Payment details
            for payment in self.payment_line_ids:
                payment_line = self.env['mbk_pms.contract.payment.line'].create(
                    {'contract_id': contract_id.id, 'service_id': payment.service_id.id, 'name': 'Cheque',
                     'note': payment.name, 'ref_date': payment.ref_date, 'payment_mode': 'chq', 'from_date': payment.from_date, 'to_date': payment.to_date,
                     'amount': payment.amount, 'days': payment.days, })
                payment_line.onchange_service_id()
                payment_line.onchange_payment_mode()

            contract_id.onchange_net_tax()
            contract_id.onchange_net_amount()

            self.contract_id = contract_id
            self.state = 'done'
            return {
                'name': 'Lease Contract',
                'res_model': 'mbk_pms.contract',
                'view_mode': 'form',
                'res_id': contract_id.id,
                'context': {'default_contract_id': contract_id.id},
                'domain': [('contract_id', '=', contract_id.id), ],
                'target': 'current',
                'type': 'ir.actions.act_window',
            }


class PMSCRenewalOfferUnitLines(models.Model):
    _name = 'mbk_pms.lease_offer.unit.line'
    _description = 'Unit Details'

    lease_offer_id = fields.Many2one('mbk_pms.lease_offer', string='Renewal Offer Reference', required=True,
                                     ondelete='cascade',
                                     index=True, copy=False)
    unit_id = fields.Many2one('mbk_pms.unit', string='Unit', domain="[('state', '=', 'available')]", readonly=True)
    service_id = fields.Many2one('mbk_pms.service', string='Services', required=True,
                                 domain="[('category', '=', 'rent')]", readonly=True)
    name = fields.Char(string='Unit Details', required=True)
    unit_type_id = fields.Many2one(related='unit_id.type_id', string='Type')
    property_id = fields.Many2one(related='unit_id.property_id', string='Property')
    original_rent = fields.Float(string="Rent", default=0)
    discount = fields.Float(string="Discount", default=0)
    agreement_rent = fields.Float(string="Agreement Rent", default=0, readonly=True, store=True)
    is_tax = fields.Boolean(string="Tax")
    tax_id = fields.Many2one('account.tax', string='Taxes', domain="[('type_tax_use', '=', 'sale')]", readonly=True, store=True)
    tax_amount = fields.Float(string="Tax Amount", default=0, readonly=True, store=True)
    net_rent = fields.Float(string="Net Rent", default=0, readonly=True, store=True)
    company_id = fields.Many2one(related='lease_offer_id.company_id', string='Company')

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
        if self.unit_id.name:
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


class PMSRenewalOfferServiceLines(models.Model):
    _name = 'mbk_pms.lease_offer.service.line'
    _description = 'Service Details'

    lease_offer_id = fields.Many2one('mbk_pms.lease_offer', string='Renewal Offer Reference', required=True,
                                     ondelete='cascade',
                                     index=True, copy=False)
    service_id = fields.Many2one('mbk_pms.service', string='Services', required=True,
                                 domain="[('category', '=', 'service')]")
    name = fields.Char(string='Service Details', required=True)
    amount = fields.Float(string="Amount", default=0)
    is_tax = fields.Boolean(string="Tax", default=True)
    tax_id = fields.Many2one('account.tax', string='Taxes', domain="[('type_tax_use', '=', 'sale')]")
    tax_amount = fields.Float(string="Tax Amount", default=0, readonly=True, store=True)
    net_amount = fields.Float(string="Net Amount", default=0, readonly=True, store=True)
    is_separate_chq = fields.Boolean(string="Separate Cheque")
    is_one_time = fields.Boolean(string="One Time")
    company_id = fields.Many2one(related='lease_offer_id.company_id', string='Company')

    @api.onchange('service_id')
    def onchange_service_id(self):
        if self.service_id:
            self.is_tax = self.service_id.is_tax
            self.is_one_time = self.service_id.is_one_time
            self.is_separate_chq = self.service_id.is_separate_chq
        else:
            self.is_tax = False
        if self.service_id.name:
            self.name = self.service_id.name

        if self.service_id.price:
            self.amount = self.service_id.price
        else:
            self.amount = 0.00

    @api.onchange('is_tax')
    def onchange_is_tax(self):
        if self.lease_offer_id.unit_line_ids[0].property_id.state_id:
            state_id = self.lease_offer_id.unit_line_ids[0].property_id.state_id
        elif self.lease_offer_id.state_id:
            state_id = self.lease_offer_id.unit_line_ids[0].property_id.state_id
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

    @api.onchange('amount', 'tax_id')
    def onchange_tax(self):
        if self.is_tax and self.tax_id:
            self.tax_amount = (self.amount * self.tax_id.amount) / 100
        else:
            self.tax_amount = 0.0
        self.net_amount = self.amount + self.tax_amount


class PMSRenewalOfferDepositLines(models.Model):
    _name = 'mbk_pms.lease_offer.deposit.line'
    _description = 'Security Deposit Details'

    lease_offer_id = fields.Many2one('mbk_pms.lease_offer', string='Renewal Offer Reference', required=True,
                                     ondelete='cascade',
                                     index=True, copy=False)
    deposit_id = fields.Many2one('mbk_pms.service', string='Deposit Type', required=True,
                                 domain="[('category', '=', 'deposit')]")
    name = fields.Char(string='Description', required=True)
    amount = fields.Float(string="Amount", default=0)
    chq_type = fields.Selection([('blank', 'Blank Dated Cheque'), ('dated', 'Dated Cheque'), ], string='Cheque Type',
                                copy=False, default='blank', help="""Cheque Type""")
    company_id = fields.Many2one(related='lease_offer_id.company_id', string='Company')
    is_separate_chq = fields.Boolean(string="Separate Cheque")

    @api.onchange('deposit_id')
    def onchange_deposit_id(self):
        if self.deposit_id:
            self.is_separate_chq = self.deposit_id.is_separate_chq
            if self.deposit_id.description:
                self.name = self.deposit_id.description


class PMSRenewalOfferPaymentSchedule(models.Model):
    _name = 'mbk_pms.lease_offer.payment.line'
    _description = 'Payment Schedule Details'

    lease_offer_id = fields.Many2one('mbk_pms.lease_offer', string='Renewal Offer Reference', required=True,
                                     ondelete='cascade', index=True, copy=False)
    service_id = fields.Many2one('mbk_pms.service', string='Service', required=True)
    name = fields.Char(string='Description', copy=False)
    note = fields.Text(string='Remarks', copy=False)
    ref_date = fields.Date(string='Date', copy=False)
    amount = fields.Float(string="Amount", default=0)
    from_date = fields.Date(string='From Date', copy=False)
    to_date = fields.Date(string='To Date', copy=False)
    days = fields.Float(string='Days', copy=False)
    company_id = fields.Many2one(related='lease_offer_id.company_id', string='Company')

    @api.onchange('service_id')
    def onchange_service_id(self):
        if self.service_id:
            self.name = self.service_id.description
