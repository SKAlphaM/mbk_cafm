# -*- coding: utf-8 -*-

import ast
from datetime import date, datetime, timedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError


class FMMaterialRequest(models.Model):
    _name = 'mbk_fm.material_request'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _description = 'FM Material Request'

    name = fields.Char(string='Material Request No', tracking=True, default='Draft', copy=False)
    request_summary = fields.Char(string='Request Summary', tracking=True, default='New')
    request_date = fields.Date(string='Request Date', default=fields.Date.context_today, copy=False)
    ticket_id = fields.Many2one('mbk_fm.ticket', string='Ticket', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('1', 'Level 1 Approval'),
        ('2', 'Level 2 Approval'),
        ('refuse', 'Rejected'),
        ('active', 'Active'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, copy=False, tracking=True, default='draft',
        help="""* When the material Request is created the status is \'Draft\'
                    \n* If the material Request is under confirmed, the status is \'Active\'.
                    \n* If the Material Request is completed then status is set to \'Done\'.
                    \n* When user cancel Material Request the status is \'cancelled\'.""")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    note = fields.Text('Notes')
    owner_user_id = fields.Many2one('res.users', string='Created by User', default=lambda s: s.env.uid, copy=False)
    request_date_time = fields.Datetime('Request Date Time', tracking=True, default=fields.Datetime.now,
                                    help="Date the Material team plans the Material.  It should not differ much from the Request Date.")
    unit_id = fields.Many2one(related='ticket_id.unit_id', string='Unit Location')
    property_id = fields.Many2one(related='ticket_id.property_id', string='Property')
    state_id = fields.Many2one(related='ticket_id.state_id', string='Emirate')
    team_id = fields.Many2one(related='ticket_id.team_id', string='Maintenance Team')
    equipment_id = fields.Many2one(related='ticket_id.equipment_id', string='Equipment', ondelete='restrict', index=True)
    customer_id = fields.Many2one(related='ticket_id.customer_id', string='Tenant')
    store_user_id = fields.Many2one('res.users', string='Store in-charge', tracking=True, domain=lambda self: [("id", "in", self.env.ref('stock.group_stock_user').users.ids), ('id', '!=', 2)])
    active = fields.Boolean(string="Active", default=True, tracking=True)
    request_line_ids = fields.One2many('mbk_fm.material_request.line', 'mr_id', string='Material Request Lines', required=True,
                                       states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)
    sub_location = fields.Char(string='Location of repair ', copy=False)
    use_store_item = fields.Boolean(string='Use from Inventory', default=0, copy=False, tracking=True)
    mr_ref_id = fields.Integer(string='Reference ID')
    # Example computed fields for button visibility
    show_approve_button = fields.Boolean(compute='_compute_show_approve_button')

    @api.depends('state')
    def _compute_show_approve_button(self):
        for rec in self:
            rec.show_approve_button = False
            if rec.state in ['1', '2']:
                state_as_int = int(rec.state)
                approval_matrix = self.env['mbk_approval.matrix_line'].search([('document', '=', 'mr'), ('sequence', '=', state_as_int), ('active', '=', True)], limit=1)
                if approval_matrix and self.env.uid in approval_matrix.approver_ids.ids:
                    rec.show_approve_button = True

    @api.model
    def create(self, vals):
        # context: no_log, because subtype already handle this
        request = super(FMMaterialRequest, self).create(vals)
        return request

    def write(self, vals):
        # Check if trying to archive while in 'active' or 'done' state
        if vals.get('active') == False and any(rec.state in ['active', 'done'] for rec in self):
            raise UserError(_("You cannot archive a document that is in 'Active' or 'Done' state."))
        # Overridden to reset the kanban_state to normal whenever
        # the stage (stage_id) of the Material Request changes.
        no = ''
        if 'state' in vals and vals['state'] == 'active':
            if self.name in ["Draft", "New"]:
                vals['name'] = self.env['ir.sequence'].next_by_code('mbk_fm.material_request')
                no = vals['name']
            else:
                no = self.name
        res = super(FMMaterialRequest, self).write(vals)
        if 'state' in vals and vals['state'] in ['draft', 'cancel']:
            self.activity_unlink(['mbk_fm.mail_act_fm_material_request'])
        return res

    def action_cancel(self):
        if self.filtered(lambda ticket: ticket.state != 'draft'):
            raise UserError(_("Can not cancel Material Request which are not in 'Draft' state."))
        else:
            self.write({'state': 'cancel'})

    def action_done(self):
        for rec in self.request_line_ids:
            rec.qty_delivered = rec.product_uom_qty
        self.write({'state': 'done'})
        self.activity_feedback(['mbk_fm.mail_act_fm_material_request'], feedback="Material Issued")

    def action_submit_approval(self):
        if not self.request_line_ids:
            raise UserError(_("Material details is missing"))
        if not self.store_user_id:
            raise UserError(_("Store in-charge is missing"))
        if self.request_line_ids.filtered(lambda line: line.product_uom == False):
            raise UserError(_("Please select the UOM for the product."))
        if_approval_required = self.env['ir.config_parameter'].get_param('mbk_fm.material_request_approval_required')
        if if_approval_required:
            approval_matrix = self.env['mbk_approval.matrix'].search([('document', '=', 'mr'), ('active', '=', True)], limit=1)
            if not approval_matrix:
                raise UserError(_("Approval Matrix not found for Material Request."))
            am_line = self.env['mbk_approval.matrix_line'].search([('matrix_id', '=', approval_matrix.id), ('sequence', '=', 1)], limit=1)
            if not am_line:
                raise UserError(_("Approval Matrix First Level not found for Material Request."))
            if not am_line.approver_ids:
                raise UserError(_("Approval Matrix First Level Approval not found for Material Request."))
            if not am_line.activity_user_id:
                raise UserError(_("Approval Activity User not found for Material Request."))
            self.write({'state': '1'})
            self.activity_schedule(
                'mbk_fm.mail_act_fm_mr_approval',
                fields.Datetime.now().date(),
                note=f"Material Request for ticket '{self.ticket_id.name}' is awaiting approval.",
                user_id=am_line.activity_user_id.id)
        else:
            self.action_confirm()

    def action_approve(self):
        if self.state in ('1', '2'):
            state_as_int = int(self.state)
            next_state = state_as_int + 1
            approval_matrix = self.env['mbk_approval.matrix'].search([('document', '=', 'mr'), ('active', '=', True)], limit=1)
            if not approval_matrix:
                raise UserError(_("Approval Matrix not found for Material Request."))
            am_line = self.env['mbk_approval.matrix_line'].search([('matrix_id', '=', approval_matrix.id), ('sequence', '=', state_as_int)], limit=1)
            am_next_line = self.env['mbk_approval.matrix_line'].search([('matrix_id', '=', approval_matrix.id), ('sequence', '=', next_state)], limit=1)
            if not am_line or self.env.uid not in am_line.approver_ids.ids:
                raise UserError(_("You are not authorized to approve this Material Request."))
            if not am_next_line:
                self.action_confirm()
                self.activity_feedback(['mbk_fm.mail_act_fm_mr_approval'], feedback="Material Request Approved")
            else:
                self.write({'state': str(next_state)})
                self.activity_feedback(['mbk_fm.mail_act_fm_mr_approval'], feedback="Material Request Approved for level " + str(state_as_int))
                self.activity_schedule(
                    'mbk_fm.mail_act_fm_mr_approval',
                    fields.Datetime.now().date(),
                    note=f"Material Request for ticket '{self.ticket_id.name}' is awaiting approval.",
                    user_id=am_next_line.activity_user_id.id)
        else:
            raise UserError(_("Material Request is not in approval state."))

    def action_confirm(self):
        if self.request_line_ids.filtered(lambda line: not line.product_uom):
            raise UserError(_("Please select the UOM for the product."))
        if self.request_line_ids:
            self.write({'state': 'active'})
        else:
            raise UserError(_("Material details is missing"))

    def action_draft(self):
        self.write({'state': 'draft'})

    @api.onchange('ticket_id')
    def onchange_ticket_id(self):
        if self.ticket_id:
            if self.request_summary == "New":
                self.request_summary = 'Material request created against ' + self.ticket_id.name
            self.sub_location = self.ticket_id.sub_location
        if self.ticket_id.team_id.store_user_id:
            self.store_user_id = self.ticket_id.team_id.store_user_id
        else:
            self.store_user_id = 2

    def action_reject_update_state_wizard(self):
        return {
            'name': 'Update Status',
            'res_model': 'mbk_fm.status_wizard',
            'view_mode': 'form',
            'context': {'default_doc_id': self.id, 'default_status': 'refuse', 'default_label_name': 'Reject', 'default_model_name': 'mr'},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_reject(self):
        if self.filtered(lambda mr: mr.state in ('1', '2')):
            self.write({'state': 'refuse'})
            self.activity_unlink(['mbk_fm.mail_act_fm_mr_approval'])
        else:
            raise UserError(_("Material Request is not in approval state."))


class FMMaterialRequestLines(models.Model):
    _name = 'mbk_fm.material_request.line'
    _description = 'FM Material Request Line'

    mr_id = fields.Many2one('mbk_fm.material_request', string='Material Request Reference', required=True, ondelete='cascade', index=True, copy=False)
    name = fields.Text(string='Description', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', domain="[('category_id', '=', product_uom_category_id)]", required=True)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', string='Unit Category')
    qty_delivered = fields.Float(string='Issued Qty', copy=False, digits='Product Unit of Measure', default=0.0)
    state = fields.Selection(related='mr_id.state', string='Material Request Status', copy=False, store=True)
    ticket_id = fields.Many2one(related='mr_id.ticket_id', string='Ticket No')
    note = fields.Text(string='Remarks')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id.uom_id.id:
            self.product_uom = self.product_id.uom_id.id
        if self.product_id.description_purchase:
            self.name = self.product_id.description_purchase
        else:
            self.name = self.product_id.name

    @api.onchange('qty_delivered')
    def onchange_qty_delivered(self):
        if self.qty_delivered > self.product_uom_qty:
            raise UserError(_("Qty should be less than or equal to requested qty"))







