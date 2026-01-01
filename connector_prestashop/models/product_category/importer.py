# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import datetime
import logging

from odoo import _, fields
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import external_to_m2o, mapping, only_create

_logger = logging.getLogger(__name__)
try:
    from prestapyt import PrestaShopWebServiceError
except ImportError:
    _logger.debug("Cannot import from `prestapyt`")


class ProductCategoryMapper(Component):
    _name = 'prestashop.product.category.import.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.product.category'

    direct = [
        ('description', 'description'),
        ('link_rewrite', 'link_rewrite'),
        ('meta_description', 'meta_description'),
        ('meta_keywords', 'meta_keywords'),
        ('meta_title', 'meta_title'),
        (external_to_m2o('id_shop_default'), 'default_shop_id'),

    ]

    # @mapping
    # def default_shop_id(self, record):
    #     return {'default_shop_id': self.env['prestashop.shop'].search([], limit=1).id}

    @mapping
    def map_boolean_fields(self, record):
        map_values = {'0': False,
                      '1': True}
        return {'active_ext': map_values[record.get('active', '0')],
                'position': int(record.get('position', '0'))
                }

    @mapping
    def is_root_category(self, record):
        return {'is_root_category': record.get('is_root_category', False)}

    @only_create
    @mapping
    def name(self, record):
        if record['name'] is None:
            return {'name': ''}
        return {'name': record['name']}

    @mapping
    def name_translation(self, record):
        if record['name'] is None:
            return {'name_translation': ''}
        return {'name_translation': record['name']}

    @mapping
    def parent_id(self, record):
        if record['id_parent'] == '0':
            return {}
        category = self.binder_for('prestashop.product.category').to_internal(
            record['id_parent'], unwrap=True)
        return {
            'parent_id': category.id,
        }

    @mapping
    def data_add(self, record):
        if record["date_add"] == "0000-00-00 00:00:00":
            return {"date_add": fields.Datetime.now()}
        return {"date_add": self.backend_record.to_utc_datetime(record["date_add"])}

    @mapping
    def data_upd(self, record):
        if record["date_upd"] == "0000-00-00 00:00:00":
            return {"date_upd": fields.Datetime.now()}
        return {"date_upd": self.backend_record.to_utc_datetime(record["date_upd"])}


class ProductCategoryImporter(Component):
    _name = 'prestashop.product.category.importer'
    _inherit = 'prestashop.translatable.importer'
    _apply_on = 'prestashop.product.category'

    _translatable_fields = [
        'name',
        'description',
        'link_rewrite',
        'meta_description',
        'meta_keywords',
        'meta_title'
    ]

    def _import_dependencies(self):
        record = self.prestashop_record
        if record['id_parent'] != '0':
            try:
                self._import_dependency(record['id_parent'],
                                        'prestashop.product.category')
            except PrestaShopWebServiceError as err:
                parent_id = record["id_parent"]
                category_id = record["id"]
                msg = _(
                    """Parent category %(category_id)s
                    for `%(parent_id)s`
                    cannot be imported. Error: %(err)s"""
                )
                binder = self.binder_for()
                binder.to_internal(category_id)
                # TODO add activity to warn about this failure
                _logger.warning(msg % (category_id, parent_id, err))


class ProductCategoryBatchImporter(Component):
    _name = 'prestashop.product.category.batch.importer'
    _inherit = 'prestashop.batch.importer'
    _apply_on = 'prestashop.product.category'


# As same product can belong to different category, merging will result in chaos
class ProductCategoryMatchImporter(Component):
    _name = 'prestashop.product.category.match.importer'
    _inherit = 'prestashop.match.importer'
    _apply_on = 'prestashop.product.category'

    _no_merging_needed = True
    _update_with_ps_values = True
    # _erp_field = "name"
    # _ps_field = "name"
    #
    # def _odoo_domain_to_consider(self, ps_dict):
    #     res = super()._odoo_domain_to_consider(ps_dict)
    #     categ_binder = self.binder_for()
    #     if ps_dict["id_parent"] and ps_dict["id_parent"] != "0":
    #         parent_categ_id = categ_binder.to_internal(
    #             ps_dict["id_parent"], unwrap=True
    #         )
    #         res += [("parent_id", "=", parent_categ_id.id)]
    #     return res
    #
    # def compare_function(self, ps_val, erp_val, ps_dict, erp_dict):
    #     if ps_val == erp_val:
    #         return True
    #     else:
    #         return super().compare_function(ps_val, erp_val, ps_dict, erp_dict)


class ProductCategoryBatchMatchImporter(Component):
    _name = 'prestashop.product.category.batch.match.importer'
    _inherit = 'prestashop.batch.match.importer'
    _apply_on = 'prestashop.product.category'
