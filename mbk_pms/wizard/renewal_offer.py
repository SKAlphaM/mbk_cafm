# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError


class PMSRenewalOfferWizard(models.TransientModel):
    _name = 'mbk_pms.renewal_offer_wizard'
    _description = 'Renewal Offer Contract Selection'

    contract_id = fields.Many2one('mbk_pms.contract', string='Contract No', required=True, domain="[('state', '=', 'open'), ('renewed_contract_id', '=', False), ('renewal_offer_id', '=', False)]")
    partner_id = fields.Many2one(related='contract_id.partner_id', string='Tenant')
    units = fields.Char(related='contract_id.units', string='Units')
    property_id = fields.Many2one(related='contract_id.property_id', string='Property')
    expiry_date = fields.Date(related='contract_id.expiry_date', string='Lease Expiry Date')
    parent_net_rent_amount = fields.Monetary(related='contract_id.net_rent_amount', string='Rent Amount')
    parent_total_deposit = fields.Monetary(related='contract_id.total_deposit', string='Security Deposit')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id,
                                  store=True)

    def action_create_renewal_offer(self):

        return










