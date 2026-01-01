# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os.path

import os

from odoo import models, fields
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, m2o_to_external

from odoo import _


class ProductImageExporter(Component):
    _name = 'prestashop.product.image.exporter'
    _inherit = 'prestashop.exporter'
    _apply_on = 'prestashop.product.image'

    def _export_dependencies(self):
        if self.binding.owner_model == 'product.category':
            product_categ = self.env['product.category'].browse(
                self.binding.owner_id)
            self._export_dependency(
                product_categ,
                'prestashop.product.category')
            return
        product_tmpl = False
        if self.binding.owner_model == 'product.product':
            product_tmpl = self.env['product.product'].browse(
                self.binding.owner_id).product_tmpl_id
        elif self.binding.owner_model == 'product.template':
            product_tmpl = self.env['product.template'].browse(
                self.binding.owner_id)
        self._export_dependency(
            product_tmpl,
            'prestashop.product.template')

    def _run(self, fields=None):
        """ Flow of the synchronization, implemented in inherited classes"""
        assert self.binding_id
        assert self.binding

        has_to_skip =  self._has_to_skip()
        if has_to_skip:
            return has_to_skip

        # export the missing linked resources
        self._export_dependencies()
        map_record = self.mapper.map_record(self.binding)
        if self.prestashop_id:
            record = map_record.values()
            if not record:
                return _('Nothing to export.')
            # special check on data before export
            self._validate_data(record)
            self.prestashop_id = self._update(record)
        else:
            record = map_record.values(for_create=True)
            if not record:
                return _('Nothing to export.')
            # special check on data before export
            self._validate_data(record)
            self.prestashop_id = self._create(record)
            self._after_export()
        # if (
        #         exported_vals
        #         and exported_vals.get("prestashop")
        #         and exported_vals["prestashop"].get("image")
        # ):
        #     self.prestashop_id = int(exported_vals["prestashop"]["image"].get("id"))
        #
        # self._link_image_to_url()
        message = _("Record exported with ID %s on Prestashop.")
        return message % self.prestashop_id


class ProductImageExportMapper(Component):
    _name = 'prestashop.product.image.export.mapper'
    _inherit = 'prestashop.export.mapper'
    _apply_on = 'prestashop.product.image'

    direct = [
        ('name', 'name'),
    ]

    def _get_file_name(self, record):
        """
        Get file name with extension from depending storage.
        :param record: browse record
        :return: string: file name.extension.
        """
        file_name = record.filename or record.name
        if not file_name:
            storage = record.storage
            if storage == 'url':
                file_name = os.path.splitext(
                    os.path.basename(record.url))
            elif storage == 'db':
                file_name = '%s_%s.jpg' % (
                    record.owner_model.replace('.', '_'),
                    record.owner_id)
                file_name = os.path.splitext(
                    os.path.basename(file_name))
            elif storage == 'file':
                file_name = os.path.splitext(
                    os.path.basename(record.path))
        return file_name

    @mapping
    def source_image(self, record):
        storage = record.storage  # TODO fix
        content = getattr(
            record.odoo_id, "_get_image_from_%s" % storage)()
        return {'content': content}

    @mapping
    def product_id(self, record):
        if record.owner_model == 'product.category':
            product_categ = record.env['product.category'].browse(
                record.owner_id)
            binder = self.binder_for('prestashop.product.category')
            ps_categ_id = binder.to_external(product_categ, wrap=True)
            return {'id_categories': ps_categ_id,
                    'id_category': ps_categ_id}
        if record.owner_model == 'product.product':
            product_tmpl = record.env['product.product'].browse(
                record.owner_id).product_tmpl_id
        else:
            product_tmpl = record.env['product.template'].browse(
                record.owner_id)
        binder = self.binder_for('prestashop.product.template')
        ps_product_id = binder.to_external(product_tmpl, wrap=True)
        return {'id_products': ps_product_id,
            'id_product': ps_product_id,
            'cover': int(record.front_image)}

    #     @mapping
    #     def extension(self, record):
    #         return {'extension': record.extension or list(self._get_file_name(record))[-1]}

    @mapping
    def legend(self, record):
        return {'legend': self.backend_record.get_slug(record.name)}

    @mapping
    def filename(self, record):
        file_name = record.filename
        if not file_name:
            file_name = self.backend_record.get_slug(self._get_file_name(record))
        if file_name.split('.')[-1].upper() not in ['JIF', 'JPG', 'JPEG', 'PNG']:
            file_name += '.jpg'
        return {'filename': file_name}
