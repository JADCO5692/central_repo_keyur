
{
    'name': "Custom NPC",
    'version': '18.0.0.38',
    'category': 'CRM',
    'summary': "Custom NPC",
    'description': """
        Custom NPC
    """, 
    'depends': ['mail','account','npc_crm','sale','sale_subscription'],
    'data': [
        "security/ir.model.access.csv",
        "views/account_move.xml",
        "views/product_template.xml",
        "views/crm_lead_view.xml",
        "views/sale_order.xml",
        "views/res_partner_view.xml",
        "views/project_task_type.xml",
		'wizard/vendor_selection_view.xml'
    ], 
    'installable': True,
    'application': False,
    'assets': {
        'web.assets_backend': [
            'custom_npc/static/src/js/ChatterExt.js',
            'custom_npc/static/src/xml/ChatterExt.xml'
        ],
    },
    'license': 'LGPL-3',
}
