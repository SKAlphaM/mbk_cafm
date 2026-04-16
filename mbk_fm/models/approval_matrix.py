from odoo import models, fields, api


class MBKApprovalMatrix(models.Model):
    _name = 'mbk_approval.matrix'
    _description = 'Approval Matrix'

    name = fields.Char(string="Name", required=True, help="Name of the approval matrix.")
    document = fields.Selection([('mr', 'Material Request'), ], string="Model")
    active = fields.Boolean(default=True, string="Active", help="Whether this matrix is active or not.")
    matrix_line_ids = fields.One2many('mbk_approval.matrix_line', 'matrix_id', string="Matrix Lines")


class MBKApprovalMatrixLine(models.Model):
    _name = 'mbk_approval.matrix_line'
    _description = 'Approval Matrix Line'

    matrix_id = fields.Many2one('mbk_approval.matrix', string="Matrix", ondelete="cascade", required=True, index=True)
    document = fields.Selection(related='matrix_id.document', string="Model ID")
    active = fields.Boolean(related='matrix_id.active', string="Active")
    sequence = fields.Integer(string="Sequence", help="Order of the approval level.")
    criteria = fields.Char(string="Criteria", help="Criteria to meet this approval level.")
    approver_ids = fields.Many2many('res.users', string="Approvers", help="Users who can approve at this level.")
    activity_user_id = fields.Many2one('res.users', string="Activity User", help="User to whom the activity is assigned.")