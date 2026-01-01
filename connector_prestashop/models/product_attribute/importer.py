# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

_logger = logging.getLogger(__name__)


# try:
#     from odoo.addons.connector_prestashop.prestapyt import PrestaShopWebServiceError
# except ImportError:
#     _logger.debug('Cannot import from `prestapyt`')


class ProductAttributeImportMapper(Component):
    _name = 'prestashop.product.attribute.import.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.product.attribute'

    direct = [
        ('name', 'name'),
        ('public_name', 'public_name'),
        ('group_type', 'group_type'),
        ('position', 'prestashop_position')
    ]

    #     @only_create
    #     @mapping
    #     def odoo_id(self, record):
    #         name = self.name(record)
    #         binding = self.env['product.attribute'].search(
    #             [('name', '=', name)],
    #             limit=1,
    #         )
    #         if binding:
    #             return {'odoo_id': binding.id}

    @mapping
    def create_variant(self, record):
        # seems the best way. If we do it in automatic, we could have too much variants
        # compared to prestashop if we got more thant 1 attributes, which seems
        # totally possible. If we put no variant, and we delete one value on prestashop
        # product won't be inative by odoo
        # with dynamic, prestashop create it on product import, odoo inactive it if
        # deleted on prestashop...
        # We avoid "You cannot change the Variants Creation Mode of the attribute"
        # error by not changing the attribute when there is existing record
        # odoo_id = self.odoo_id(record)
        default_language = self.backend_record.default_language or "en_US"
        model = self.env["product.attribute"].with_context(
            active_test=False, lang=default_language, prefetch_fields=False
        )

        binding = model.search(
            [("name", "=", record["name"])],
            limit=1,
        )
        if not binding:
            return {"create_variant": "dynamic"}

    @mapping
    def is_color_group(self, record):
        display_type = record['group_type']
        map_values = {'0': False,
                      '1': True}
        if map_values[record.get('is_color_group', '0')] == True:
            return {"display_type": 'color'}
        else:
            return {"display_type": display_type}


class ProductCombinationOptionImporter(Component):
    _name = 'prestashop.product.attribute.importer'
    _inherit = 'prestashop.translatable.importer'
    _apply_on = 'prestashop.product.attribute'

    _translatable_fields = ['name', 'public_name']

    def _import_values(self, attribute_binding):
        record = self.prestashop_record
        option_values = record.get('associations', {}).get(
            'product_option_values', {}).get(
            self.backend_record.get_version_ps_key('product_option_value'), [])
        if not isinstance(option_values, list):
            option_values = [option_values]
        for option_value in option_values:
            self._import_dependency(
                option_value['id'],
                'prestashop.product.attribute.value'
            )

    def _after_import(self, binding):
        res = super()._after_import(binding)
        self._import_values(binding)
        return res


class ProductAttributeMatchImporter(Component):
    _name = 'prestashop.product.attribute.match.importer'
    _inherit = 'prestashop.match.importer'
    _apply_on = 'prestashop.product.attribute'

    _erp_field = 'name'  # prestashop_bind_ids
    _ps_field = 'name'

    def compare_function(self, ps_val, erp_val, ps_dict, erp_dict):
        if ps_val == erp_val:
            return True
        else:
            return super().compare_function(ps_val, erp_val, ps_dict, erp_dict)


class ProductAttributeBatchMatchImporter(Component):
    _name = 'prestashop.product.attribute.batch.match.importer'
    _inherit = 'prestashop.batch.match.importer'
    _apply_on = 'prestashop.product.attribute'


class ProductAttributeValueImportMapper(Component):
    _name = 'prestashop.product.attribute.value.import.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.product.attribute.value'

    direct = [
        ('name', 'name'),
        ('position', 'prestashop_position')
    ]

    #     @only_create
    #     @mapping
    #     def odoo_id(self, record):
    #         attribute_binder = self.binder_for(
    #             'prestashop.product.attribute'
    #         )
    #         attribute = attribute_binder.to_internal(
    #             record['id_attribute_group'],
    #             unwrap=True
    #         )
    #         assert attribute
    #         binding = self.env['product.attribute.value'].search(
    #             [('name', '=', record['name']),
    #              ('attribute_id', '=', attribute.id)],
    #             limit=1,
    #         )
    #         if binding:
    #             return {'odoo_id': binding.id}

    @mapping
    def attribute_id(self, record):
        binder = self.binder_for('prestashop.product.attribute')
        attribute = binder.to_internal(record['id_attribute_group'], unwrap=True)
        return {'attribute_id': attribute.id}

    @mapping
    def color(self, record):
        if record.get('color', False):
            return {"html_color": record['color']}

class ProductAttributeValueImporter(Component):
    _name = 'prestashop.product.attribute.value.importer'
    _inherit = 'prestashop.translatable.importer'
    _apply_on = 'prestashop.product.attribute.value'

    _translatable_fields = ['name']


class ProductAttributeValueMatchImporter(Component):
    _name = 'prestashop.product.attribute.value.match.importer'
    _inherit = 'prestashop.match.importer'
    _apply_on = 'prestashop.product.attribute.value'

    _erp_field = 'name'  # prestashop_bind_ids
    _ps_field = 'name'

    #     def _ps_fields_to_consider(self):
    #         return super(ProductCombinationOptionValueMergeImporter, self)._ps_fields_to_consider() +['name','id_attribute_group']

    def _odoo_domain_to_consider(self, ps_dict):
        res = super()._odoo_domain_to_consider(ps_dict)
        attribute_binder = self.binder_for('prestashop.product.attribute')
        attribute = attribute_binder.to_internal(
            ps_dict['id_attribute_group'],
            unwrap=True
        )
        res += [('attribute_id', '=', attribute.id)]
        return res

    def _odoo_fields_to_consider(self):
        return super()._odoo_fields_to_consider() + ['name', 'attribute_id']

    def compare_function(self, ps_val, erp_val, ps_dict, erp_dict):
        if ps_val == erp_val:
            return True
        else:
            return super().compare_function(ps_val, erp_val, ps_dict, erp_dict)


class ProductAttributeValueBatchMatchImporter(Component):
    _name = 'prestashop.product.attribute.value.batch.match.importer'
    _inherit = 'prestashop.batch.match.importer'
    _apply_on = 'prestashop.product.attribute.value'
