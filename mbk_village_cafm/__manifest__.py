# -*- coding: utf-8 -*-
{
    'name': "Workers Village Management",
    'summary': """Workers Village Management System""",
    'description': """Workers Village Management System""",
    'author': "Siyad Sharafudeen",
    'website': "http://www.mbkgroup.com",
    'category': 'Workers Management',
    'version': '0.0.1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'contacts', 'mail','website'],
    # always loaded
    'data': [

        'security/ir.model.access.csv',
        'views/tenant_management_views.xml',
        'views/mess_hall_templates.xml',
        'views/tenant_track.xml',

    ],
    'assets': {
        'web.assets_frontend': [
            'mbk_village_cafm/static/src/css/mess_hall.scss',
            'mbk_village_cafm/static/src/js/mess_hall.js',
        ],
    },
    # 'demo': [
    #     'demo/demo.xml',
    # ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
