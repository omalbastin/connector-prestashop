# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import OrderedDict

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

_logger = logging.getLogger(__name__)


class ProductTemplateExporter(Component):
    _inherit = 'prestashop.product.template.exporter'

    def delete_existing_images(self, images, product_ps_id):
        if not images:
            return
        if product_ps_id and product_ps_id > 0:
            image_adapter = self.component(usage='backend.adapter', model_name='prestashop.product.image')
            # psapi = image_adapter.client
            resource = '/images/products/%s' % product_ps_id
            deleted_image = False
            # image_adapter.delete(resource)
            try:
                res = image_adapter.search(resource, options=None)
                for ext_ps_id in res:
                    rem_resource = "%s/%s" % (resource, ext_ps_id)
                    image_adapter.delete(rem_resource)
                    # self.env['prestashop.product.image'].export_delete_record(self.backend_record,
                    #                                                                        ext_ps_id, rem_resource)
                deleted_image = True
            except:
                pass
                # if deleted_image:
        images.mapped('prestashop_bind_ids').with_context(connector_no_export=True
                                                          ).prestashop_id = 0

    def delete_image_before_export(self):
        if self.prestashop_id and self.backend_record.import_export_images in ['export', 'import_export']:
            if self.binding.ps_active:
                self.delete_existing_images(self.binding.image_ids, self.prestashop_id)

    def _before_export(self):
        super()._before_export()
        self.delete_image_before_export()

    def export_image_dependencies(self):
        if self.backend_record.import_export_images in ['export', 'import_export']:
            if self.binding.prestashop_id and self.binding.image_ids:
                default_image = self.binding.image_ids.filtered('front_image')[:1]
                if not default_image:
                    default_image = self.binding.image_ids[:1]
                    default_image.with_context(connector_no_export=True).front_image = True
                self._export_dependency(default_image, 'prestashop.product.image')
                (self.binding.odoo_id.image_ids - default_image).with_context(connector_no_export=True
                                                                              ).front_image = False

    def _export_dependencies(self):
        """ Export the dependencies for the product"""
        super()._export_dependencies()
        self.export_image_dependencies()

    # def _not_in_variant_images(self, image):
    #     images = []
    #     if len(self.binding.combinations_ids) > 1:  # product_variant_ids
    #         for product in self.binding.combinations_ids:  # product_variant_ids
    #             images.extend(product.image_ids.ids)
    #     return image.id not in images

    def check_images(self):
        if self.binding.image_ids:
            # image_binder = self.binder_for('prestashop.product.image')
            default_image = self.binding.image_ids.filtered('front_image')[:1]
            image_binding = self._export_dependency(default_image, 'prestashop.product.image')
            # image_binding.with_delay().export_record()
            for image in self.binding.image_ids:
                if image == default_image:
                    continue
                image_binding = self._export_dependency(image, 'prestashop.product.image')


    def _after_export(self):
        super()._after_export()
        if self.backend_record.import_export_images in ['export', 'import_export']:
            self.check_images()


class ProductTemplateExportMapper(Component):
    _inherit = 'prestashop.product.template.export.mapper'

    @mapping
    def default_image(self, record):
        if self.backend_record.import_export_images in ['export', 'import_export']:
            if record.ps_active and record.image_ids:
                default_image = record.image_ids.filtered('front_image')[:1]
                # if not default_image and record.image_ids:
                #     for first_image in record.image_ids:
                #         default_image = first_image
                #         break
                #     default_image.front_image = True
                if not default_image:
                    default_image = record.image_ids[:1]
                binder = self.binder_for('prestashop.product.image')
                ps_image_id = binder.to_external(default_image, wrap=True)
                if ps_image_id:
                    return {'id_default_image': ps_image_id}
        else:
            return {}