# -*- coding: utf-8 -*-
{
    'name': "Facility Management",
    'summary': """Streamlines maintenance processes with preventive and corrective methods for improved property management.""",
    'description': """
    Odoo Facility Management Module
    ================================
    The Odoo Facility Management Module is a sophisticated solution tailored for the seamless management of commercial spaces. It encompasses a wide range of functionalities designed to ensure facilities are maintained in a healthy, safe, and fully operational state.

    Core Functionalities:
    - **Preventive Maintenance Management**: Automates the scheduling of routine inspections and maintenance tasks to prevent equipment failures and extend asset lifespan.
    - **Corrective Maintenance Management**: Provides a streamlined process for addressing unexpected equipment breakdowns, minimizing downtime and operational disruptions.
    - **Maintenance Ticket Registration**: Facilitates the efficient logging and tracking of maintenance requests, ensuring timely responses to facility-related issues.
    - **Scheduling and Timesheet Tracking**: Enhances planning and workforce management by tracking maintenance schedules and employee timesheets.
    - **Material Requests Management**: Manages the requisition and approval of materials needed for maintenance tasks, ensuring efficient resource allocation.
    - **Hold and Approval Statuses**: Implements hold and approval workflows for maintenance activities, offering greater control over the maintenance process.
    - **Warranty Tracking**: Keeps track of equipment warranties, enabling timely maintenance and replacements under warranty conditions.

    Benefits:
    - Ensures a healthy, safe, and functional environment for facility occupants.
    - Optimizes asset utilization and reduces maintenance costs through effective preventive and corrective maintenance strategies.
    - Enhances operational efficiency with streamlined maintenance processes and workflows.
    - Improves decision-making with comprehensive reporting on maintenance activities and facility performance.

    This module is designed to cater to the needs of organizations looking to optimize their facility management practices, offering tools and insights to maintain high standards of facility operation and security.
        """,
    'author': "Rinto Antony",
    'website': "http://www.mbkgroup.com",
    'category': 'Facility Management',
    'version': '0.1.0',
    # any module necessary for this one to work correctly
    'depends': ['base', 'contacts', 'mail', 'mbk_pms', 'product', 'hr', 'stock'],
    # always loaded
    'data': [
        'security/fm.xml',
        'security/ir.model.access.csv',
        'data/mail_data.xml',
        'views/menu.xml',
        'wizard/start_timer_view.xml',
        'wizard/end_timer_view.xml',
        'wizard/update_state_view.xml',
        'wizard/fm_update_state.xml',
        'wizard/maintenance_request_wizard.xml',
        'wizard/idle_technician_view.xml',
        'views/ticket_view.xml',
        'views/team_view.xml',
        'views/type_view.xml',
        'views/approval_matrix.xml',
        'views/equipment_view.xml',
        'views/equipment_category_view.xml',
        'views/user_view.xml',
        'views/material_request_view.xml',
        'views/fm_property_view.xml',
        'views/vacant_unit_view.xml',
        'views/activity_view.xml',
        'views/res_config_settings.xml',
        'data/mbk_fm_cron.xml',
        'report/report_list.xml',
        'report/ticket_report.xml',
        'report/ticket_image_report.xml',
        'report/mr_report.xml',
        'report/maintainence_report_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mbk_fm/static/src/js/timer.js',
        ]},
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
