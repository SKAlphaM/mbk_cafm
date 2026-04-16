# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = ['res.config.settings']

    mbk_pms_lease_offer_approver_id = fields.Many2one('res.users', string='Lease Offer Approver', default=2, config_parameter='mbk_pms_lease_offer_approver_id')












