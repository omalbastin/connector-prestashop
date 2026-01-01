# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.addons.component.core import Component

from odoo.addons.connector.components.mapper import mapping


class ProductTemplateManufacturerExportMapper(Component):
    _inherit = 'prestashop.product.template.export.mapper'

    @mapping
    def manufacturer(self, record):
        if record.manufacturer:
            binder = self.binder_for('prestashop.manufacturer')
            value = binder.to_external(record.manufacturer.id, wrap=True)
            if value:
                return {'id_manufacturer': value}
        return {}


class ProductTemplateManufacturerExporter(Component):
    _inherit = 'prestashop.product.template.exporter'

    def _export_manufacturer(self):
        record = self.binding.manufacturer
        if record:
            # TODO: can't we use ManufacturerExporter right away?
            manuf_binding = self._export_dependency(
                record, 'prestashop.manufacturer')
            # PS needs an address anyway

    #             addresses = record.child_ids #or [record, ]
    #             for address in addresses:
    #                 self._export_dependency(
    #                     address,
    #                     'prestashop.manufacturer.address',
    #                     bind_values={'prestashop_partner_id': manuf_binding.id})

    def _export_dependencies(self):
        super(ProductTemplateManufacturerExporter, self)._export_dependencies()
        self._export_manufacturer()
