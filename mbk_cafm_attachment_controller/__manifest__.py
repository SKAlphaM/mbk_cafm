# -*- coding: utf-8 -*-
{
    'name': "MBK Production Attachment Controller",
    'summary': """Connecting attachment from main to cafm""",
    'description': "",
    'author': "Siyad Sharaf",
    'website': "http://www.mbkgroup.com",
    'category': 'Attachment',
    'version': '15.0',
    # any module necessary for this one to work correctly
    'depends': ['base','mail','contacts' ],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/fm.xml',
        'views/mbk_cafm_attachment.xml',
        'views/menu.xml',

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
