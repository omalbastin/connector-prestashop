##############################################################################
#
#    ODOO, Open Source Management Solution
#    Copyright (C) 2020 - Today Omal Bastin (O4) <omalbastin@gmail.com>
#    For more details, check COPYRIGHT and LICENSE files
#
##############################################################################
{
    "name": "Sync Images from Prestashop",
    "summary": """
    Sync Images from Prestashop
        """,
    "description": """
Sync Images from Prestashop
    """,
    "license": "AGPL-3",
    'author': 'Omal Bastin (O4)',
    "website": "https://github.com/OCA/connector-prestashop",
    "category": "Others",
    "version": "18.0.1.0.0",
    "depends": [
        "connector_prestashop_catalog_manager",
        "product_multi_image",  # oca/product-attribute
        "category_image",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/queue_job_data.xml",
        "views/prestashop_backend_view.xml",
        "views/product_view.xml",
        "views/image_view.xml",

    ],
    "demo": [],
    "auto_install": True,
    "installable": True
}
