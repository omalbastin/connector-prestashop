# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import external_to_m2o, mapping

_logger = logging.getLogger(__name__)


# class ProductCategoryMapper(Component):
#     _name = "prestashop.product.category.import.mapper"
#     _inherit = "prestashop.product.category.import.mapper"
#
#     @mapping
#     def image(self, record):
#         category_image_adapter = self.component(
#             usage="backend.adapter", model_name="prestashop.category.image"
#         )
#
#         try:
#             return {"image_1920": category_image_adapter.read(record["id"])}
#         except Exception:
#             return {}

class ProductCategoryImporter(Component):
    _name = 'prestashop.product.category.importer'
    _inherit = 'prestashop.product.category.importer'

    def _after_import(self, binding):
        super()._after_import(binding)
        if self.backend_record.import_export_images in ['import', 'import_export']:
            self.import_images(binding)

    def import_images(self, binding):
        self.env['prestashop.product.image'].with_delay(
            priority=10,
            description=f"Import image for category with ID {self.prestashop_id}",
        ).import_product_image(
            self.backend_record,
            'categories',
            self.prestashop_id,
            "-%s" % self.prestashop_id
        )