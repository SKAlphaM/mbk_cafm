# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PmsUnitTypes(models.Model):
    _name = 'mbk_pms.unit_type'
    _description = 'Unit Types'

    name = fields.Char(string='Unit Type Name', required=True)
    code = fields.Char(string='Unit Type Code', required=True)
    description = fields.Text(string='Description')
    ref_id = fields.Integer(string='Reference ID')
    active = fields.Boolean(string="Active", default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)


class PmsUnitNos(models.Model):
    _name = 'mbk_pms.unit_no'
    _description = 'Unit Nos'

    name = fields.Char(string='Unit Nos', required=True)
    code = fields.Char(string='Floor')
    description = fields.Text(string='Description')
    ref_id = fields.Integer(string='Reference ID')
    active = fields.Boolean(string="Active", default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)