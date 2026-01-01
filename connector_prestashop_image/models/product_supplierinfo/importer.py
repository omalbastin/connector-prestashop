# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

_logger = logging.getLogger(__name__)


# try:
#     from odoo.addons.connector_prestashop.prestapyt import PrestaShopWebServiceError
# except:
#     _logger.debug('Cannot import from `prestapyt`')


class SupplierMapper(Component):
    _name = "prestashop.supplier.mapper"
    _inherit = "prestashop.supplier.mapper"

    @mapping
    def image(self, record):
        supplier_image_adapter = self.component(
            usage="backend.adapter", model_name="prestashop.supplier.image"
        )

        try:
            return {"image_1920": supplier_image_adapter.read(record["id"])}
        except Exception as e:
            return {}


class SupplierImporter(Component):
    """Import one simple record"""

    _name = "prestashop.supplier.importer"
    _inherit = "prestashop.supplier.importer"

    def _create(self, record):
        try:
            return super()._create(record)
        except ZeroDivisionError as e:
            del record["image"]
            return super()._create(record)
