# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


import logging
import mimetypes

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

_logger = logging.getLogger(__name__)
try:
    from prestapyt import PrestaShopWebServiceError
except ImportError:
    _logger.debug("Cannot import from `prestapyt`")


class ProductImageMapper(Component):
    _name = 'prestashop.product.image.import.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.product.image'

    direct = [
    ]

    def _image_name_exists(self, code):
        model = self.env['base_multi_image.image']
        image_ids = model.search([
            ('name', '=', code),
        ], limit=1)
        return len(image_ids) > 0

    @mapping
    def from_template(self, record):
        if 'id_product' in record:
            odoo_model = 'product.template'
            binder = self.binder_for('prestashop.product.template')
            odoo_record = binder.to_internal(record['id_product'], unwrap=True)

            name = '%s_%s' % (odoo_record.name, record['id_image'])
        elif 'id_category' in record:
            odoo_model = 'product.category'
            binder = self.binder_for('prestashop.product.category')
            odoo_record = binder.to_internal(record['id_category'], unwrap=True)
            name = '%s_%s' % (odoo_record.name, record['id_category'])
        else:
            raise

        res = {'owner_id': odoo_record.id, 'owner_model': odoo_model, 'name': name}
        if not self._image_name_exists(name):
            return res
        i = 1
        current_name = '%s_%d' % (name, i)
        while self._image_name_exists(current_name):
            i += 1
            current_name = '%s_%d' % (name, i)
        res.update({'name': current_name})
        return res

    @mapping
    def extension(self, record):
        return {'extension': mimetypes.guess_extension(record['type'])}

    @mapping
    def image_url(self, record):
        return {'url': record['full_public_url']}

    @mapping
    def filename(self, record):
        if 'id_product' in record:
            return {'filename': '%s.jpg' % record['id_image']}
        elif 'id_category' in record:
            return {'filename': 'category_%s.jpg' % record['id_category']}
        else:
            raise
    #
    # @mapping
    # def owner_model(self, record):
    #     return {"owner_model": "product.template"}

    # @mapping
    # def image_1920(self, record):
    #     return {"image_1920": record["content"]}

    @mapping
    def storage(self, record):
        return {'storage': 'url'}
        # return {'storage': 'db'}


class ProductImageImporter(Component):
    _name = 'prestashop.product.image.importer'
    _inherit = 'prestashop.importer'
    _apply_on = 'prestashop.product.image'

    def _get_prestashop_data(self):
        """ Return the raw PrestaShop data for ``self.prestashop_id`` """
        return self.backend_adapter.read(self.resource, self.resource_id, self.image_id)

    def run(self, resource, resource_id, image_id, **kwargs):
        self.resource = resource
        self.resource_id = resource_id
        self.image_id = image_id
        if resource == 'products':
            binder = self.binder_for('prestashop.product.template')
            model = 'product.template'
        elif resource == 'categories':
            binder = self.binder_for('prestashop.product.category')
            model = 'product.category'
        else:
            raise
        resource_record = binder.to_internal(resource_id, unwrap=True)
        try:
            result = super().run(image_id, **kwargs)
        except PrestaShopWebServiceError as error:

            # if hasattr(resource_record, 'prestashop_default_image_id'):
            #     if str(resource_record.prestashop_default_image_id) != str(image_id):
            #         return "Image import Failed"
            # _logger.warning(
            #     "Import of main image id %s for %s %s failed: %s",
            #     image_id, resource, resource_id, error
            # )
            return "Import of main image id %s for %s %s failed: %s" % (
                image_id, resource, resource_id, error)
        if not resource_record.image_1920:
            resource_record._compute_image_1920()

        # if hasattr(resource_record, 'prestashop_default_image_id'):
        #     if str(resource_record.prestashop_default_image_id) == str(image_id):
        #         image_binder = self.binder_for("prestashop.product.image")
        #         image = image_binder.to_internal(image_id, unwrap=True)
        #         if image:
        #             resource_record.image_1920 = image.image_1920
        return result

    def _after_import(self, binding):
        super()._after_import(binding)
        record = binding.odoo_id
        record.with_delay().storage_to_filestore()


