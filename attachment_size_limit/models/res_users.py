# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. 
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class Users(models.Model):
    _inherit = 'res.users'

    attachment_size_limit = fields.Float(
        string="Attachment Size Limit (MB)",
        digits=(5, 1),
        help="""Configured Attachment Size Limit (IN MB) for user,
        not allowed to user if attachment size is greater then configured"""
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
