# -*- coding: utf-8 -*-
###############################################
# EzTech Software & Consultancy Inc. (c) 2025
###############################################
{
    'name': 'Custom Amber',
    'version': '1.00',
    "license": "OPL-1",    
    'category': 'Generic Modules/Customization',
    'summary': 'Amber Customizations.',
    'description': """
        Amber Customizations.
    """,
    'author': 'Logiz Information Technology Solutions',
    'website': 'http://www.logiz.cloud',
    'depends': [
        'ez_leaves',
        'ez_timekeeping_payroll',
    ],
    'init_xml': [],
    'data': [        
        # 'security/security.xml',
        # 'security/ir.model.access.csv',
        'payroll_view.xml',
    ],
    'demo': [
        #'hr_demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'qweb': [],
}
