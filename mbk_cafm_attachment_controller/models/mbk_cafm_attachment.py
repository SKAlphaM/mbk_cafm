# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MBKAttachment(models.Model):
    _name = 'mbk_cafm.attachment'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'MBK Production Attachment Controller'
    _rec_name = 'name'

    remote_server_id = fields.Char(string="Remote Server ID", tracking=True)
    name = fields.Char('Name', required=True, tracking=True)
    description = fields.Text('Description', tracking=True)
    res_name = fields.Char('Resource Name', compute='_compute_res_name')
    res_model = fields.Char('Resource Model', tracking=True)
    res_field = fields.Char('Resource Field', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
                                 default=lambda self: self.env.company, tracking=True)

    doc_attachment_id = fields.Many2many('ir.attachment', 'doc_attach_rel',
                                         'doc_id', 'attach_id3',
                                         string="Attachment",
                                         help='You can attach the copy of your document',
                                         copy=False)
    source_created_user = fields.Char(string="Source Created User")
    source_created_date = fields.Datetime(string="Source Created Date")

    @api.depends('name')
    def _compute_res_name(self):
        for rec in self:
            rec.res_name = rec.name







































