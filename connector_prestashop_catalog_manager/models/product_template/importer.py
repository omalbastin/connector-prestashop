# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import (
    mapping,
    external_to_m2o
)

_logger = logging.getLogger(__name__)

try:
    from bs4 import BeautifulSoup
except ImportError:
    _logger.debug('Cannot import `bs4`')


class TemplateMapperInherit(Component):
    _inherit = 'prestashop.product.template.import.mapper'

    direct = [
        # ('weight', 'weight'),
        # ('wholesale_price', 'wholesale_price'),
        # ('wholesale_price', 'standard_price'),
        (external_to_m2o('id_shop_default'), 'default_shop_id'),
        ('link_rewrite', 'link_rewrite'),
        ('reference', 'reference'),
        ('upc', 'upc'),
        # ('available_for_order', 'available_for_order'),
        # ('on_sale', 'on_sale'),
        ("low_stock_threshold", "low_stock_threshold"),
        # above copied from connector_prestashop
        ('meta_title', 'meta_title'),
        # ('meta_description','meta_description'),
        ('meta_keywords', 'meta_keywords'),
        ('low_stock_alert', 'low_stock_alert'),
        #         ('state','ps_state'),
        #         ('available_for_order', 'available_for_order'),
        #         ('on_sale', 'on_sale'),
    ]

    @staticmethod
    def sanitize_html(content):
        content = BeautifulSoup(content, 'html.parser')
        # Prestashop adds both 'lang="fr-ch"' and 'xml:lang="fr-ch"'
        # but Odoo tries to parse the xml for the translation and fails
        # due to the unknow namespace
        for child in content.find_all(lambda tag: tag.has_attr('xml:lang')):
            del child['xml:lang']
        return content.prettify()

    @mapping
    def meta_description(self, record):
        return {
            'meta_description': self.sanitize_html(
                record.get('meta_description', '')),
        }

