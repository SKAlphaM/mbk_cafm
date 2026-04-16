# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. 
# See LICENSE file for full copyright and licensing details.

import base64
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Attachment(models.Model):
    _inherit = 'ir.attachment'

    def _get_file_size_custom(self, file_binary):
        file_size_in_bytes = len(base64.b64decode(file_binary))
        return "{0:0.1f}".format(file_size_in_bytes / 1000.0 / 1000.0)

    @api.model_create_multi
    def create(self, vals_list):
        current_user = self.env.user
        if not self._context.get('website_id') and current_user.has_group("attachment_size_limit.attachment_size_limit_grp"):
            custom_error = ''
            is_file_big = False
            for vals in vals_list:
                if vals.get('datas'):
                    file_size_in_mb = self._get_file_size_custom(vals['datas'])
                    if current_user.attachment_size_limit < float(file_size_in_mb):
                        is_file_big = True
                        custom_error += '- %s\n' %(vals['name'])
            if is_file_big:
                raise ValidationError(
                    _('Below file(s) exceed attachment size limit (max size allowed %0.1f MB):')%(current_user.attachment_size_limit) + '\n' + _(custom_error))
        return super(Attachment, self).create(vals_list)

    def write(self, vals):
        current_user = self.env.user
        if not self._context.get('website_id') and vals.get('datas') and current_user.has_group("attachment_size_limit.attachment_size_limit_grp"):
            file_size_in_mb = self._get_file_size_custom(vals['datas'])
            if current_user.attachment_size_limit < float(file_size_in_mb):
                custom_error = ' - ' + vals['name'] if vals.get('name') else rec.name or ''
                raise ValidationError(_('Below file(s) exceed attachment size limit (max size allowed %0.1f MB):')%(current_user.attachment_size_limit) + '\n' + _(custom_error))
        return super(Attachment, self).write(vals)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
