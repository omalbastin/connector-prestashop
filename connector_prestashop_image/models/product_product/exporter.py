# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import OrderedDict

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

_logger = logging.getLogger(__name__)


class ProductCombinationExport(Component):
    _inherit = 'prestashop.product.product.exporter'

    def _export_images(self):
        if self.binding.image_ids:
            for image_line in self.binding.image_ids:
                self._export_dependency(
                    image_line,
                    'prestashop.product.image')

    def _export_dependencies(self):
        """ Export the dependencies for the product"""
        super()._export_dependencies()
        if self.backend_record.import_export_images in ['export', 'import_export']:
            self._export_images()


class ProductCombinationExportMapper(Component):
    _inherit = 'prestashop.product.product.export.mapper'

    def _get_combination_image(self, record):
        images = []
        image_binder = self.binder_for('prestashop.product.image')
        for image in record.image_ids:
            image_ext_id = image_binder.to_external(image.id, wrap=True)
            if image_ext_id:
                images.append({'id': image_ext_id})
        return images

    @mapping
    def associations(self, record):
        result = super().associations(record)
        associations = result.get('associations')
        if not associations:
            associations = OrderedDict()
            result['associations'] = associations
        associations.update({
            'images': {
                'image': self._get_combination_image(record) or False
            }
        })
        return result


