import base64

from odoo import http, fields, _
from odoo.http import request, Response

import base64
import os

from odoo import http, api, SUPERUSER_ID
from odoo.http import request,_logger
from odoo.tools import config


class ContractReportController(http.Controller):

    @http.route(
        '/public/<string:db>/attachment/<string:token>',
        type='http',
        auth="public",
        methods=['GET'],
        csrf=False,
    )
    def public_attachment_download(self, db, token, **kwargs):
        """
        Public download route for attachments using access_token.
        Works with both DB-stored (datas) and filestore-stored (store_fname) attachments.
        """

        # Make sure we are in the correct database
        try:
            registry = http.request.registry
        except Exception:
            import odoo
            registry = odoo.registry(db)

        if not registry:
            return request.not_found()

        # Open cursor for the given DB
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})

            # Search for the attachment by access_token
            att = env['ir.attachment'].search([('access_token', '=', token)], limit=1)
            _logger.info("Attachment Got IT %s ",att)
            if not att:
                return request.not_found()

            # Fetch file content
            filecontent = b''
            if att.datas:
                filecontent = base64.b64decode(att.datas)
            elif att.store_fname:
                # File is in filestore
                path = config.filestore(db)
                filepath = os.path.join(path, att.store_fname)
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        filecontent = f.read()
                else:
                    return request.not_found()

            # Return file
            filename = att.name or "download"
            return request.make_response(
                filecontent,
                headers=[
                    ('Content-Type', 'application/octet-stream'),
                    ('Content-Disposition', f'attachment; filename="{filename}"'),
                ]
            )

