# © 2016-TODAY Omal Bastin(O4 ODOO) <omalbastin@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if

_logger = logging.getLogger(__name__)


class ProductCategoryListener(Component):
    _name = 'product.category.listener'
    _inherit = 'prestashop.connector.listener'
    _apply_on = 'product.category'

    def _get_category_export_fields(self):
        # fields which should trigger an export of the categories
        return [
            'name',
            'parent_id',
            'name_translation'
        ]

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if set(fields) & set(self._get_category_export_fields()):
            for binding in record.prestashop_bind_ids:
                binding.with_delay(priority=20,
                                   description=f"Export {binding.odoo_id._name} with ID {binding.odoo_id.id}",
                                   ).export_record(field_names=fields)

    @skip_if(lambda self, record: self.no_connector_export(record))
    def on_record_unlink(self, record):
        if not hasattr(record, 'prestashop_bind_ids') or not record.prestashop_bind_ids:
            return
        for binding in record.prestashop_bind_ids:
            binding.export_delete_record(binding.backend_id, binding.prestashop_id)


class PrestashopProductCategoryListener(Component):
    _name = 'prestashop.product.category.listener'
    _inherit = 'prestashop.connector.listener'
    _apply_on = 'prestashop.product.category'

    def _get_category_export_fields(self):
        # fields which should not trigger an export of the products
        # but an export of their inventory
        return [
            'name',
            'name_translation',
            # 'prestashop_backend_id',
            'parent_id',
            'description',
            'link_rewrite',
            'meta_description',
            'meta_keywords',
            'meta_title',
            'position'
        ]

    @skip_if(lambda self, record, fields, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        identity = record.backend_id.generate_identity_key(record)
        record.with_delay(priority=20,
                          description=f"Export {record.odoo_id._name} with ID {record.odoo_id.id}",
                          identity_key=identity).export_record()

    @skip_if(lambda self, record, fields, **kwargs: self.no_connector_export(record) or \
                                                    self.need_to_export(record, fields=fields))
    def on_record_write(self, record, fields=None):
        if set(fields) & set(self._get_category_export_fields()):
            identity = record.backend_id.generate_identity_key(record)
            record.with_delay(priority=20,
                              description=f"Export {record.odoo_id._name} with ID {record.odoo_id.id}",
                              identity_key=identity).export_record(field_names=fields)

    @skip_if(lambda self, record: self.no_connector_export(record))
    def on_record_unlink(self, record):
        record.export_delete_record(record.backend_id, record.prestashop_id)
