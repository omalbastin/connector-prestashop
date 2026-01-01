# © 2016-TODAY Omal Bastin(Steigend IT Solutions) <omalbastin@steigendit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

from odoo import models

_logger = logging.getLogger(__name__)
try:
    from prestapyt import PrestaShopWebServiceError
except ImportError:
    _logger.debug("Cannot import from `prestapyt`")


class PrestashopProductCombination(models.Model):
    _inherit = "prestashop.product.product"

    def set_product_image_variant(self, backend, combination_ids, **kwargs):  # TODO move to new module
        with backend.work_on(self._name) as work:
            importer = work.component(usage="prestashop.importer")
            return importer.set_variant_images(combination_ids, **kwargs)

