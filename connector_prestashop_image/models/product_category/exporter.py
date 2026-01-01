# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, m2o_to_external

_logger = logging.getLogger(__name__)


class ProductCategoryExporter(Component):
    _inherit = 'prestashop.product.category.exporter'

    def check_images(self):
        if self.binding.image_ids:
            for image in self.binding.image_ids:
                self._export_dependency(
                    image,
                    'prestashop.product.image')

    def _after_export(self):
        if self.backend_record.import_export_images in ['export', 'import_export']:
            self.check_images()
