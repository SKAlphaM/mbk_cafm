# -*- coding: utf-8 -*-
# from odoo import http


# class MbkPms(http.Controller):
#     @http.route('/mbk_pms/mbk_pms/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mbk_pms/mbk_pms/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('mbk_pms.listing', {
#             'root': '/mbk_pms/mbk_pms',
#             'objects': http.request.env['mbk_pms.mbk_pms'].search([]),
#         })

#     @http.route('/mbk_pms/mbk_pms/objects/<model("mbk_pms.mbk_pms"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mbk_pms.object', {
#             'object': obj
#         })
