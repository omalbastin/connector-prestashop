# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

_logger = logging.getLogger(__name__)


class ManufacturerImportMapper(Component):
    _inherit = 'prestashop.product.template.import.mapper'

    @mapping
    def extras_manufacturer(self, record):
        if record.get('id_manufacturer'):
            binder = self.binder_for('prestashop.manufacturer')
            value = binder.to_internal(record['id_manufacturer'], unwrap=True)
            if value:
                return {'manufacturer': value.id}
        return {}


class ManufacturerProductTemplateImporter(Component):
    _inherit = 'prestashop.product.template.importer'

    def import_manufacturer(self, manufacturer_id):
        if manufacturer_id and int(manufacturer_id):
            self._import_dependency(manufacturer_id, 'prestashop.manufacturer')

    def _import_dependencies(self):
        super()._import_dependencies()
        self.import_manufacturer(self.prestashop_record.get("id_manufacturer"))
