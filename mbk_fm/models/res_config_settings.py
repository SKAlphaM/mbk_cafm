# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mbk_fm_material_request_approval_required = fields.Boolean(
        string='Material Request Approval Required',
        config_parameter='mbk_fm.material_request_approval_required'
    )

    