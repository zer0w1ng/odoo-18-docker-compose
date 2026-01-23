# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Helpdesk Management - Extended",
    "summary": """
        Helpdesk Extended Features/Customization for Helpdesk Management Module""",
    "version": "18.0.1.16.4",
    "license": "AGPL-3",
    "category": "After-Sales",
    "author": "Regulus Berdin / rberdin@gmail.com",
    "depends": [
        "base",
        "web",
        "helpdesk_mgmt",
        "hr",
        "ez_timekeeping_payroll",
        "ez_leaves"
    ],
    "data": [
        'security/ir.model.access.csv',
        'helpdesk_view.xml',
    ],
    "demo": [],
    "development_status": "Production/Stable",
    "application": True,
    "installable": True,
}
