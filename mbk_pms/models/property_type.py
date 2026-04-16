# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PmsPropertyTypes(models.Model):
    _name = 'mbk_pms.property_type'
    _description = 'Property Type Master'

    name = fields.Char(string='Property Type Name', required=True)
    code = fields.Char(string='Property Type Code', required=True)
    description = fields.Text(string='Description')
    ref_id = fields.Integer(string='Reference ID')
    active = fields.Boolean(string="Active", default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    # tag_ids = fields.Many2many('event.tag', string="Tags")


