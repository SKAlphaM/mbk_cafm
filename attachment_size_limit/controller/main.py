# -*- coding: utf-8 -*-

import json
import os

from odoo import http
from odoo.http import request, serialize_exception
from odoo.addons.web.controllers.binary import Binary
from odoo.addons.mail.controllers.attachment import AttachmentController as MailAttachmentController


class DiscussController(MailAttachmentController):
    @http.route('/mail/attachment/upload', methods=['POST'], type='http', auth='public')
    def mail_attachment_upload(self, ufile, thread_id, thread_model, is_pending=False, **kwargs):
        current_user = request.env.user
        if current_user.has_group('attachment_size_limit.attachment_size_limit_grp'):
            files = request.httprequest.files.getlist('ufile')
            custom_error = 'Below file(s) exceed attachment size limit (max size allowed %0.1f MB):' % (
                current_user.attachment_size_limit
            )
            is_file_big = False
            for file_open in files:
                file_size_in_mb = "{0:0.1f}".format(os.fstat(file_open.fileno()).st_size / 1000.0 / 1000.0)
                if current_user.attachment_size_limit < float(file_size_in_mb):
                    custom_error += " - " + file_open.filename + ' (%0.1f MB)' % float(file_size_in_mb)
                    is_file_big = True

            if is_file_big:
                return request.make_response(
                    data=json.dumps({'error': custom_error}),
                    headers=[('Content-Type', 'application/json')]
                )
        return super().mail_attachment_upload(
            ufile=ufile,
            thread_id=thread_id,
            thread_model=thread_model,
            is_pending=is_pending,
            **kwargs
        )


class Binary(Binary):
    @http.route('/web/binary/upload_attachment', type='http', auth="user")
    def upload_attachment(self, model, id, ufile, callback=None):
        current_user = request.env.user
        if current_user.has_group('attachment_size_limit.attachment_size_limit_grp'):
            files = request.httprequest.files.getlist('ufile')
            custom_error = 'Below file(s) exceed attachment size limit (max size allowed %0.1f MB):' % (
                current_user.attachment_size_limit
            )
            is_file_big = False
            for file_open in files:
                file_size_in_mb = "{0:0.1f}".format(os.fstat(file_open.fileno()).st_size / 1000.0 / 1000.0)
                if current_user.attachment_size_limit < float(file_size_in_mb):
                    custom_error += " - " + file_open.filename + ' (%0.1f MB)' % float(file_size_in_mb)
                    is_file_big = True

            if is_file_big:
                out = """<script language="javascript" type="text/javascript">
                            var win = window.top.window;
                            win.jQuery(win).trigger(%s, %s);
                        </script>"""
                args = [{
                    'custom_error': custom_error,
                    'error': custom_error,
                }]
                return out % (json.dumps(callback), json.dumps(args))

        return super().upload_attachment(callback=callback, model=model, id=id, ufile=ufile)