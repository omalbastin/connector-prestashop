# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import OrderedDict

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

_logger = logging.getLogger(__name__)



class ProductCombinationOptionExport(Component):
    _name = 'prestashop.product.attribute'
    _inherit = 'translation.prestashop.exporter'
    _apply_on = 'prestashop.product.attribute'


class ProductCombinationOptionExportMapper(Component):
    _name = 'prestashop.product.attribute.export.mapper'
    _inherit = 'translation.prestashop.export.mapper'
    _apply_on = 'prestashop.product.attribute'

    direct = [
        ('prestashop_position', 'position'),
        ('group_type', 'group_type'),
    ]

    _translatable_fields = [
        ('name', 'name'),
        ('name', 'public_name'),
    ]


class ProductCombinationOptionValueExport(Component):
    _name = 'prestashop.product.attribute.value.exporter'
    _inherit = 'translation.prestashop.exporter'
    _apply_on = 'prestashop.product.attribute.value'

    def _export_dependencies(self):
        """ Export the dependencies for the record"""
        #         attribute_id = self.binding.attribute_id.id
        # export product attribute
        #         binder = self.binder_for('prestashop.product.attribute')
        self._export_dependency(
            self.binding.attribute_id,
            'prestashop.product.attribute')
        #         if not binder.to_external(attribute_id, wrap=True):
        #             exporter = self.get_connector_unit_for_model(
        #                 TranslationPrestashopExporter,
        #                 'prestashop.product.attribute')
        #             exporter.run(attribute_id)
        return


class ProductCombinationOptionValueExportMapper(Component):
    _name = 'prestashop.product.attribute.value.export.mapper'
    _inherit = 'translation.prestashop.export.mapper'
    _apply_on = 'prestashop.product.attribute.value'

    direct = [('name', 'value')]
    # handled by base mapping `translatable_fields`
    _translatable_fields = [
        ('name', 'name'),
    ]

    #     @mapping
    #     def prestashop_product_attribute_id(self, record):
    #         attribute_binder = self.binder_for(
    #             'prestashop.product.attribute.value')
    #         return {
    #             'id_feature': attribute_binder.to_external(
    #                 record.attribute_id.id, wrap=True)
    #         }

    @mapping
    def prestashop_product_group_attribute_id(self, record):
        attribute_binder = self.binder_for(
            'prestashop.product.attribute')
        return {
            'id_attribute_group': attribute_binder.to_external(
                record.attribute_id.id, wrap=True),
        }
