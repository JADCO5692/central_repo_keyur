
{
    'name': "Custom NPC",
    'version': '18.0.0.55',
    'category': 'CRM',
    'summary': "Custom NPC",
    'description': """
        Custom NPC
    """, 
    'depends': [
        'mail',
        'account',
        'npc_crm',
        'sale',
        'sale_subscription',
        'payment_fees_base',
    ],
    'data': [
        "security/ir.model.access.csv",
        "views/account_move.xml",
        "views/product_template.xml",
        "views/crm_lead_view.xml",
        "views/sale_order.xml",
        "views/res_partner_view.xml",
        "views/project_task_type.xml",
		'wizard/vendor_selection_view.xml',
        'views/payment_form.xml',
        'views/dashboard.xml',
        'views/payment_method_view.xml',
        'views/payment_form_template.xml',
		'views/portal_invoice.xml',
    ],
    'installable': True,
    'application': False,
    'assets': {
        'web.assets_backend': [
            'custom_npc/static/plugins/*',
            'custom_npc/static/src/js/ChatterExt.js',
            'custom_npc/static/src/xml/ChatterExt.xml',
            'custom_npc/static/src/dashboard/*'
        ],
    },
    'license': 'LGPL-3',
}
