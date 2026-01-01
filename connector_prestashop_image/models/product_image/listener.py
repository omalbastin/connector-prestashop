# © 2016-TODAY Omal Bastin(O4 ODOO) <omalbastin@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if

_logger = logging.getLogger(__name__)


class ProductImageListener(Component):
    _name = 'base_multi_image.image.listener'
    _inherit = 'prestashop.connector.listener'
    _apply_on = 'base_multi_image.image'

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        for backend in self.env['prestashop.backend'].search([]):
            ps_binding = self.env['prestashop.product.image'].create({
                'odoo_id': record.id,
                'backend_id': backend.id,
            })
        return

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        for binding in record.prestashop_bind_ids:
            backend = binding.backend_id
            if backend.import_export_images in ['export', 'import_export']:
                identity = binding.backend_id.generate_identity_key(binding)
                binding.with_delay(priority=20,
                                   identity_key=identity,
                                   description=f"Export {binding.odoo_id._name} with ID {binding.odoo_id.id}",
                                   ).export_record()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record, fields=None):
        """Called when a record is deleted"""
        for binding in record.prestashop_bind_ids:
            backend = binding.backend_id
            if backend.import_export_images not in ['export', 'import_export']:
                continue
            if binding.ps_product_tmpl_id:
                template = binding.ps_product_tmpl_id #TODO re work needed
                # product = binding.ps_product_tmpl_id.odoo_id
            else:
                product = self.env[record.owner_model].browse(record.owner_id)
                if product.exists():
                    template = product.prestashop_bind_ids.filtered(
                        lambda x: x.backend_id == binding.backend_id
                    )
            if not template:
                return

            work = self.work.work_on(collection=binding.backend_id)
            binder = work.component(
                usage="binder", model_name="prestashop.product.image"
            )
            prestashop_id = binder.to_external(binding)
            attributes = {
                "id_product": template.prestashop_id,
            }
            if prestashop_id:
                self.env[
                    "prestashop.product.image"
                ].with_delay(
                    description=f"Delete prestashop.product.image with ps ID {prestashop_id}",

                ).export_delete_record(
                    binding.backend_id, prestashop_id, attributes
                )


class PrestashopImageListener(Component):
    _name = 'prestashop.image.listener'
    _inherit = 'prestashop.connector.listener'
    _apply_on = ['prestashop.product.image',
                 ]

    @skip_if(lambda self, record, fields, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        backend = record.backend_id
        if backend.import_export_images in ['export', 'import_export']:
            identity = record.backend_id.generate_identity_key(record)
            record.with_delay(priority=20,
                              description=f"Export {record.odoo_id._name} with ID {record.odoo_id.id}",
                              identity_key=identity).export_record()

#     @skip_if(lambda self, record,fields, **kwargs: self.no_connector_export(record) or \
#              self.need_to_export(record, fields=fields))
#     def on_record_write(self, record, fields=None):
#         backend = record.backend_id
#         if backend.import_export_images in ['export','import_export']:
#             record.with_delay(priority=20).export_record()


# MOVED ABOVE
# class ImageUnlinkListener(Component):
#     _name = "image.unlink.listener"
#     _inherit = "prestashop.connector.listener"
#     _apply_on = [
#         "base_multi_image.image",
#     ]
#
#     @skip_if(lambda self, record: self.no_connector_export(record))
#     def on_record_unlink(self, record):
#         if not hasattr(record, "prestashop_bind_ids") or not record.prestashop_bind_ids:
#             return
#         for binding in record.prestashop_bind_ids:
#             binding.delete_record()


# TODO Do we need this?
# class PrestashopImageUnlinkListener(Component):
#     _name = "prestashop.image.unlink.listener"
#     _inherit = "prestashop.connector.listener"
#     _apply_on = [
#         "prestashop.product.image",
#         #                  'prestashop.product.template'
#     ]
#
#     @skip_if(lambda self, record: self.no_connector_export(record))
#     def on_record_unlink(self, record):
#         record.delete_record()
