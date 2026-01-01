# Copyright 2011-2013 Camptocamp
# Copyright 2011-2013 Akretion
# Copyright 2015 AvanzOSC
# Copyright 2015-2016 Tecnativa
# © 2017-2021 Omal Bastin (O4)  <omalbastin@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "PrestaShop-Odoo connector",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "base_vat",  # for vat validation on partner address
        "product_multi_category",  # oca/product-attribute
        "connector_ecommerce",  # oca/connector-ecommerce
        "purchase",
        "stock_delivery",
        # "onchange_helper",  # oca/server-tools # used in so
        #         "web_tree_dynamic_colored_field",
        #         "product_variant_supplierinfo",  # oca/product-variant
        # TODO: perhaps not needed:
        # "product_variant_cost_price",  # oca/product-variant
    ],
    "external_dependencies": {
        'python': [
            # "html2text",
            "prestapyt",
            # if circular import issue: pip install --ignore-installed git+https://github.com/prestapyt/prestapyt.git@master

            # tests dependencies
            #             "freezegun",
            #             "vcr",
            #             "bs4",
        ],
    },
    "author": "Omal Bastin (O4),"
              "Akretion,"
              "Camptocamp,"
              "AvanzOSC,"
              "Tecnativa,"
              "Mind And Go,"
              "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/connector-prestashop",
    "category": "Connector",
    'demo': [
        'demo/backend.xml',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/prestashop_security.xml',
        'data/queue_job_data.xml',
        'data/cron.xml',
        'data/product_decimal_precision.xml',
        # 'data/product_data.xml',
        'views/prestashop_backend_views.xml',
        # 'views/image_view.xml',
        'views/product_view.xml',
        'views/product_category_view.xml',
        'views/prestashop_delivery_carrier_views.xml',
        'views/prestashop_res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/account_tax_group_views.xml',
        'views/stock_view.xml',
        'views/queue_job_views.xml',
        'views/connector_prestashop_menu.xml',
        #         'data/ecommerce_data.xml',
    ],
    "installable": True,
    "application": True,
}
