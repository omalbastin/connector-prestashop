# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class SaleOrderStateMapper(Component):
    _name = 'prestashop.sale.order.state.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.sale.order.state'

    direct = [
        ('name', 'name'),
    ]
    #what about shopid??

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}


class SaleOrderStateImporter(Component):
    """ Import one translatable record """
    _name = 'prestashop.sale.order.state.importer'
    _inherit = 'prestashop.translatable.importer'
    _apply_on = 'prestashop.sale.order.state'

    _translatable_fields = [
        'name',
    ]


class SaleOrderStateBatchImporter(Component):
    _name = 'prestashop.sale.order.state.batch.importer'
    _inherit = 'prestashop.batch.importer'
    _apply_on = 'prestashop.sale.order.state'


class SaleOrderStateMatchImporter(Component):
    _name = 'prestashop.sale.order.state.match.importer'
    _inherit = 'prestashop.match.importer'
    _apply_on = 'prestashop.sale.order.state'

    _erp_field = 'name'
    _ps_field = 'name'

    def compare_function(self, ps_val, erp_val, ps_dict, erp_dict):
        if ps_val == erp_val:
            return True
        else:
            return super().compare_function(ps_val, erp_val, ps_dict, erp_dict)


class SaleOrderStateMatchBatchImporter(Component):
    _name = 'prestashop.sale.order.state.batch.match.importer'
    _inherit = 'prestashop.batch.match.importer'
    _apply_on = 'prestashop.sale.order.state'
