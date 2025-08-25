
{
    'name': "Custom NPC Commission Logs",
    'version': '18.0.0.27',
    'category': 'CRM',
    'summary': "Custom NPC Commission Logs",
    'description': """
        Custom NPC Commission Logs
    """, 
    'depends': ['mail','account','custom_npc','npc_sharetribe'],
    'data': [
        "security/ir.model.access.csv",
        "data/cron.xml",
        "data/sequence.xml",
        "views/account_move.xml",
        "views/sale_commission_logs.xml", 
    ], 
    'installable': True,
    'application': False,
    'assets': {},
    'license': 'LGPL-3',
}
