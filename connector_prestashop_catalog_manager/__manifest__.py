# Copyright 2011-2013 Camptocamp
# Copyright 2011-2013 Akretion
# Copyright 2015 AvanzOSC
# Copyright 2015-2016 Tecnativa
# Copyright 2016-Today Omal Bastin (O4) <omalbastin@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Prestashop-Odoo Catalog Manager",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "connector_prestashop"
    ],
    "author": "Omal Bastin (O4), "
              "Akretion,"
              "AvanzOSC,"
              "Tecnativa,"
              'Camptocamp SA,'
              "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/connector-prestashop",
    "category": "Connector",
    "data": [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'data/queue_job_data.xml',
        'views/product_attribute_view.xml',
        'views/product_category_view.xml',
        'views/product_template_view.xml',
        'views/prestashop_backend_view.xml',
        'wizards/export_category_view.xml',
        #         'wizards/export_multiple_products_view.xml',
        'wizards/sync_products_view.xml',
        'wizards/active_deactive_products_view.xml',
        # 'views/product_image_view.xml',
    ],
    "installable": True,
}
