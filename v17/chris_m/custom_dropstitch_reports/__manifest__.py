{
    'name':'Custom - Drop Stitch Reports',
    'version':'17.0.1.0.9',
    "development_status": "Production/Stable",
    "license": "LGPL-3",
    'category': 'Manufacturing/Manufacturing',
    'summary': (
        """
        Custom - Drop Stitch Reports
        """
    ),
    'description': """ 
            """,
    "author": "theERPbot",
    "website": "https://www.theerpbot.com",
    'images': ['static/description/img1.png'],
    'depends': [
         'mrp',
         'custom_dropstitch',
    ],
    'data':[
             'data/report_paperformat.xml',
             'report/report_label_workorder.xml',
             'views/mrp_production_view.xml',
    ],
    'installable': True,
    'application': False,
}
