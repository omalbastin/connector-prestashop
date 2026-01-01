# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, m2o_to_external

_logger = logging.getLogger(__name__)


class ProductCategoryExporter(Component):
    _name = 'prestashop.product.category.exporter'
    _inherit = 'translation.prestashop.exporter'
    _apply_on = 'prestashop.product.category'

    def _export_dependencies(self):
        """ Export the dependencies for the category"""
        category_binder = self.binder_for('prestashop.product.category')
        categories_obj = self.env['prestashop.product.category']
        self.export_parent_category(
            self.binding.parent_id, category_binder, categories_obj)

    def export_parent_category(self, category, binder, ps_categ_obj):
        if not category:
            return
        #         ext_id = binder.to_external(category, wrap=True)
        #         if ext_id:
        #             return True
        position_cat_id = ps_categ_obj.search(
            [], order='position desc', limit=1)
        obj_position = position_cat_id.position + 1
        res = {
            # 'link_rewrite': self.backend_record.get_slug(category.name),
            'position': obj_position,
        }
        self._export_dependency(
            category,
            'prestashop.product.category', bind_values=res)
        return True

    # def check_images(self):
    #     if self.binding.image_ids:
    #         image_binder = self.binder_for('prestashop.product.image')
    #         for image in self.binding.image_ids:
    #             self._export_dependency(
    #                 image,
    #                 'prestashop.product.image')
    #
    # def _after_export(self):
    #     if self.backend_record.import_export_images in ['export', 'import_export']:
    #         self.check_images()


class ProductCategoryExportMapper(Component):
    _name = 'prestashop.product.category.export.mapper'
    _inherit = 'translation.prestashop.export.mapper'
    _apply_on = 'prestashop.product.category'

    direct = [
        # (m2o_to_external('default_shop_id'), 'id_shop_default'),
        # ('active_ext', 'active_ext'),
        ('active_ext', 'active'),
        # ('position', 'position')
    ]
    # handled by base mapping `translatable_fields`
    _translatable_fields = [
        ('name_translation', 'name'),
        ('link_rewrite', 'link_rewrite'),
        ('description', 'description'),
        ('meta_description', 'meta_description'),
        ('meta_keywords', 'meta_keywords'),
        ('meta_title', 'meta_title'),
    ]

    @mapping
    def id_shop_default(self, record):
        shop_binder = self.binder_for('prestashop.shop')
        ext_shop_id = shop_binder.to_external(
            self.env['prestashop.shop'].search([], limit=1), wrap=True)
        return {'id_shop_default': ext_shop_id}

    # @mapping
    # def link_rewrite(self, record): done in deepl product translation module #managed with _Before_export
    #     res = {}
    #     get_slug = self.backend_record.get_slug
    #     records_by_language = self._get_record_by_ps_lang(record)
    #     value = {'language': []}
    #     for language_id, lrecord in records_by_language.items():
    #         value['language'].append({
    #             'attrs': {'id': str(language_id)},
    #             'value': get_slug(lrecord['name']) or ''
    #         })
    #     res['link_rewrite'] = value
    #     return res

    @mapping
    def position(self, record):
        return {'position': record.position}

    @mapping
    def parent_id(self, record):
        if not record['parent_id']:
            if record['prestashop_id'] not in [1, 2]:
                return {'id_parent': 2}
            return {}
        category_binder = self.binder_for('prestashop.product.category')
        ext_categ_id = category_binder.to_external(
            record.parent_id, wrap=True)
        return {'id_parent': ext_categ_id}
