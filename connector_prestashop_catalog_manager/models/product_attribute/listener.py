# © 2016-TODAY Omal Bastin(O4 ODOO) <omalbastin@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if

_logger = logging.getLogger(__name__)


class ProductAttributeListener(Component):
    _name = 'product.attribute.listener'
    _inherit = 'prestashop.connector.listener'
    _apply_on = ['product.attribute',
                 'product.attribute.value']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if fields:
            for binding in record.prestashop_bind_ids:
                identity = binding.backend_id.generate_identity_key(binding)
                binding.with_delay(priority=20,
                                   identity_key=identity,
                                   description=f"Export {binding.odoo_id._name} with ID {binding.odoo_id.id}",
                                   ).export_record(field_names=fields)


class PrestashopProductAttributeListener(Component):
    _name = 'prestashop.product.attribute.listener'
    _inherit = 'prestashop.connector.listener'
    _apply_on = ['prestashop.product.attribute',
                 'prestashop.product.attribute.value',
                 ]

    @skip_if(lambda self, record, fields, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        identity = record.backend_id.generate_identity_key(record)
        record.with_delay(priority=20,
                          description=f"Export {record.odoo_id._name} with ID {record.odoo_id.id}",
                          identity_key=identity).export_record(field_names=fields)

    @skip_if(lambda self, record, fields, **kwargs:
             self.no_connector_export(record) or self.need_to_export(record, fields=fields))
    def on_record_write(self, record, fields=None):
        identity = record.backend_id.generate_identity_key(record)
        record.with_delay(priority=20,
                          description=f"Export {record.odoo_id._name} with ID {record.odoo_id.id}",
                          identity_key=identity).export_record(field_names=fields)

    @skip_if(lambda self, record: self.no_connector_export(record))
    def on_record_unlink(self, record):
        if not record.prestashop_id:
            return
        record.with_delay().export_delete_record(record.backend_id, record.prestashop_id)
