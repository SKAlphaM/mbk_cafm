# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. 
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Attachment Size Limit by User',
    'version': '4.1.3',
    'price': 99.0,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'category' : 'Tools',
    'summary': """Attachment Size Limit by Users""",
    'description': """
Attachment Size Limit
Not allowed to attach greater size of file as configured
file size limit
Record attachment size limit
Attachment Size Limit by User
attachment size
size attachment
attachment limit size
document size
document size limit
document limit size
    """,
    'author': "Probuse Consulting Service Pvt. Ltd.",
    'website': "http://www.probuse.com",
    'support': 'contact@probuse.com',
    'images': ['static/description/img1.jpg'],
    'live_test_url': 'https://probuseappdemo.com/probuse_apps/attachment_size_limit/405',#'https://youtu.be/SNnBnVh-P7w',
    'depends': [
        'mail',
        'web',
    ],
    'data':[
        'security/attachment_size_security.xml',
        'views/res_users_view.xml',
#        'views/attachment_js_view.xml',
    ],
    'installable' : True,
    'application' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

