# -*- coding: utf-8 -*-
{'name': "Property Management System",
 'summary': """Property Management System for Odoo Community Edition work along with Facility Management Module""",
 'description': """
PropertyManagement System
============================================
This module enriches Odoo Community Edition by seamlessly integrating Property Management with Facility Management, offering a robust solution for managing real estate properties and maintenance operations. Designed to work in conjunction with the Facility Management module, it facilitates a detailed analysis of maintenance tasks across various dimensions, including Units, Properties, Areas, Emirates, Responsible Persons, Tenants, and more.

Key Features:
- **Master Data Management**: Manages a comprehensive set of master data including Units, Properties, Areas, and Emirates, essential for property and facility management.
- **Seamless Integration**: Ensures tight integration with the Facility Management module for cohesive management of maintenance tasks and operations.
- **Advanced Maintenance Analysis**: Enables detailed maintenance analysis by various entities such as Property, Unit, Area, responsible personnel, and Tenants, providing valuable insights for decision-making.
- **Contract and Tenant Management**: Streamlines the management of leases, contracts, and tenant relationships, enhancing operational efficiency and tenant satisfaction.
- **Customizable Reporting**: Provides customizable reporting tools to generate insights on property performance, maintenance efficiency, financial transactions, and occupancy rates.
Ideal for property managers, facility managers, and real estate businesses, this module aims to optimize property management practices, improve maintenance operations, and enhance tenant relations through comprehensive data integration and analysis.
    """,
 'author': "Rinto Antony",
 'website': "http://www.mbkgroup.com",
 # Categories can be used to filter modules in modules listing
 # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
 # for the full list
 'category': 'Property Management',
 'version': '1.0.0',
 # any module necessary for this one to work correctly
 'depends': ['base', 'contacts', 'mail', 'account'],

 # always loaded
 'data': [
     'security/ir.model.access.csv',
     'views/menu.xml',
     'views/property_type_view.xml',
     'views/property_view.xml',
     'views/unit_type_view.xml',
     'views/unit_no_view.xml',
     'views/unit_view.xml',
     'views/auh_property_view.xml',
     'views/services.xml',
     'views/contract_view.xml',
     'views/contract_payment_lines.xml',
     'views/payment_collection_view.xml',
     'views/payment_deposit_view.xml',
     'views/cheque_hold_view.xml',
     'views/process_bounced_view.xml',
     'views/cheque_replacement_view.xml',
     'views/payment_clearing_view.xml',
     'views/cheque_bounced_view.xml',
     'views/break_request_view.xml',
     'views/break_contract_view.xml',
     'views/renewal_offer_view.xml',
     'views/lease_offer_view.xml',
     'views/contract_enquiry_view.xml',
     'views/renewed_contract_view.xml',
     'views/renewal_contract_view.xml',
     'wizard/update_state_view.xml',
     'wizard/chq_hold_update_state_view.xml',
     'views/templates.xml',
     'data/data.xml',
     'data/mbk_pms_cron.xml',
     'views/res_config_settings_views.xml',
 ],
 # only loaded in demonstration mode
 'demo': [
     'demo/demo.xml',
 ],
 'installable': True,
 'application': True,
 'auto_install': False,
 'license': 'LGPL-3',
 }
