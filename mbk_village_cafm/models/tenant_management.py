import logging
import pprint
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
_logger = logging.getLogger(__name__)


class TenantManagement(models.Model):
    _name = 'mbk_village.tenant'
    _description = 'Tenant Management'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, tracking=True)
    arabic_full_name = fields.Char(string='Arabic Full Name', tracking=True)
    date_of_birth = fields.Date(string='Date of Birth', tracking=True)
    nationality = fields.Char(string='Nationality', required=False, tracking=True)
    company = fields.Char(string='Company', tracking=True)
    contact_no = fields.Char(string='Contract #', tracking=True)
    access_card = fields.Char(string='Access Card Number', copy=False, tracking=True)

    room_code = fields.Char(string='Room Code',copy=False)

    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
        ('terminated', 'Terminated')
    ], string='Status', default='pending', tracking=True)
    mess_hall_services = fields.Char(string='Mess Hall Menu', tracking=True)
    laundry_services = fields.Char(string='Laundry Services Menu', tracking=True)
    image_1920 = fields.Image(string="Tenant Image", max_width=1920, max_height=1920)
    counter_data = fields.Char(string='Counter Data', tracking=True)
    main_server_tenant_id = fields.Integer(string='Main Server Tenant ID', index=True)





