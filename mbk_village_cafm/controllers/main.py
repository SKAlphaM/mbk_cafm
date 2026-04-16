# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class MessHallController(http.Controller):

    @http.route('/mess-hall', type='http', auth='user', website=True)
    def mess_hall_page(self, **kwargs):
        return request.render('mbk_village_cafm.mess_hall_page_template', {})

    @http.route('/mess-hall/scan', type='json', auth='user', methods=['POST'], csrf=False)
    def mess_hall_scan(self, card_number=None, **kwargs):
        print("Received card number:", card_number)
        card_number = (card_number or '').strip()

        if not card_number:
            return {
                'status': 'failed',
                'message': 'Please enter or scan a valid card.',
                'tenant': {},
            }

        tenant = request.env['mbk_village.tenant'].sudo().search([
            ('access_card', '=', card_number)
        ], limit=1)

        if not tenant:
            return {
                'status': 'failed',
                'message': 'You have no access to the mess hall',
                'tenant': {}
            }
        log = request.env['mbk_village.tenant.tracking'].sudo().create({
            'tenant_id': tenant.id,
            # 'company_id': tenant.company_id.id if tenant.company_id else False,
            'action': 'mess_hall',
            'notes': 'Accessed mess hall via card scan.'
        })

        image_url = False
        if hasattr(tenant, 'image_1920') and tenant.image_1920:
            image_url = '/web/image/mbk_village.tenant/%s/image_1920' % tenant.id
        elif hasattr(tenant, 'image_1024') and tenant.image_1024:
            image_url = '/web/image/mbk_village.tenant/%s/image_1024' % tenant.id
        elif hasattr(tenant, 'image') and tenant.image:
            image_url = '/web/image/mbk_village.tenant/%s/image' % tenant.id

        tenant_code = tenant.room_code or '' if hasattr(tenant, 'room_code') else ''
        company_name = tenant.company or '' if hasattr(tenant, 'company') else ''
        menu_items = tenant.mess_hall_services or '' if hasattr(tenant, 'mess_hall_services') else ''
        counter_data = tenant.counter_data or '' if hasattr(tenant, 'counter_data') else ''

        return {
            'status': 'success',
            'message': 'Access Granted',
            'tenant': {
                'id': tenant.id,
                'name': tenant.name or '',
                'code': tenant_code,
                'company': company_name,
                'card_number': tenant.access_card or '',
                'image_url': image_url,
                'menu_items': menu_items,
                'counter_data': counter_data,
            }
        }
