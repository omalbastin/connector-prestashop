# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import (
    mapping,
    only_create,
)


class ManufacturerImporter(Component):
    _name = 'prestashop.manufacturer.importer'
    _inherit = 'prestashop.importer'
    _apply_on = 'prestashop.manufacturer'


class ManufacturerImportMapper(Component):
    _name = 'prestashop.manufacturer.import.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.manufacturer'

    direct = [
        ('name', 'name_ext'),
        ('name', 'name'),
        ('link_rewrite', 'link_rewrite')
    ]

    @mapping
    def data_add(self, record):
        if record['date_add'] == '0000-00-00 00:00:00':
            return {'date_add': fields.Datetime.now()}
        return {'date_add': self.backend_record.to_utc_datetime(record['date_add'])}

    @mapping
    def data_upd(self, record):
        if record['date_upd'] == '0000-00-00 00:00:00':
            return {'date_upd': fields.Datetime.now()}
        return {'date_upd': self.backend_record.to_utc_datetime(record['date_upd'])}

    @mapping
    def map_boolean_fields(self, record):
        map_values = {'0': False,
                      '1': True}
        return {'active_ext': map_values[record.get('active', '0')],
                }

    # @mapping
    # def supplier(self, record):
    #     return {'supplier': True}

    @mapping
    @only_create
    def assign_partner_category(self, record):
        manufacturer_categ = self.env.ref(
            'connector_prestashop_manufacturer.partner_manufacturer_tag')
        return {'category_id': [(4, manufacturer_categ.id)]}


class ManufacturerBatchImporter(Component):
    _name = 'prestashop.manufacturer.batch.importer'
    _inherit = 'prestashop.batch.importer'
    _apply_on = 'prestashop.manufacturer'


class ManufacturerMatchImporter(Component):
    _name = 'prestashop.manufacturer.match.importer'
    _inherit = 'prestashop.match.importer'
    _apply_on = 'prestashop.manufacturer'

    _erp_field = 'name'
    _ps_field = 'name'

    #     _default_fields = [(external_to_m2o('id_shop_group'), 'shop_group_id'),]

    def compare_function(self, ps_val, erp_val, ps_dict, erp_dict):
        if not ps_val and not erp_val:
            return False
        if ps_val == erp_val:
            return True
        return False


class ProductCategoryBatchMatchImporter(Component):
    _name = 'prestashop.manufacturer.batch.match.importer'
    _inherit = 'prestashop.batch.match.importer'
    _apply_on = 'prestashop.manufacturer'
