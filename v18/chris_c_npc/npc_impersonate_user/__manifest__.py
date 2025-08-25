{
    "name": "NPC Impersonate User",
    "summary": """
        Customization for Auth Impersonate Users.
    """,
    'author': "Mark Dela Cruz",
    'website': 'https://www.markdelacruz.com',
    "category": "Technical",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["web", "base", "auth_impersonate_user"],
    "demo": [],
    "data": ["views/res_users.xml", "views/res_partner.xml",
             "data/group_data.xml", "data/server_action_data.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": [],
}
