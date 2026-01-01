# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import _

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, external_to_m2o


class ShopGroupImporter(Component):
    _name = 'prestashop.shop.group.importer'
    _inherit = 'prestashop.importer'
    _apply_on = 'prestashop.shop.group'


class ShopGroupMapper(Component):
    _name = 'prestashop.shop.group.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.shop.group'

    direct = [('name', 'name')]

    @mapping
    def name(self, record):
        name = record['name']
        if name is None:
            name = _('Undefined')
        return {'name': name}


class ShopImporter(Component):
    _name = "prestashop.shop.importer"
    _inherit = "prestashop.importer"
    _apply_on = "prestashop.shop"


class ShopImportMapper(Component):
    _name = "prestashop.shop.mapper"
    _inherit = "prestashop.import.mapper"
    _apply_on = "prestashop.shop"

    direct = [
        ("name", "name"),
        (external_to_m2o("id_shop_group"), "shop_group_id"),
    ]

    @mapping
    def backend_id(self, record):
        return {"backend_id": self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def odoo_id(self, record):
        return {'odoo_id': self.backend_record.warehouse_id.id}
