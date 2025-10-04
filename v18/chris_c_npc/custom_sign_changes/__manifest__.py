
{
    'name': "Custom NPC Sign Changes",
    'version': '18.0.0.2',
    'category': 'Sign',
    'summary': "Custom NPC Sign",
    'description': """
        Custom NPC Sign Changes
    """, 
    'depends': ['sign'],
    'data': [
        "views/payment_methods.xml",
        "views/email_template_body.xml"
    ],
    'installable': True,
    'application': False,
    'assets': {
        'web.assets_frontend': [
            "/custom_sign_changes/static/src/js/doc.js"
        ],
    },
    'license': 'LGPL-3',
}