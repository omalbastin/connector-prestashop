# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import (
    mapping,
)


class TaxGroupMapper(Component):
    _name = 'prestashop.account.tax.group.import.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.account.tax.group'

    direct = [
        ('name', 'name'),
    ]

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}


class TaxGroupImporter(Component):
    _name = 'prestashop.account.tax.group.importer'
    _inherit = 'prestashop.importer'
    _apply_on = 'prestashop.account.tax.group'


class TaxGroupBatchImporter(Component):
    _name = 'prestashop.account.tax.group.batch.importer'
    _inherit = 'prestashop.batch.importer'
    _apply_on = 'prestashop.account.tax.group'


class AccountTaxGroupMatchImporter(Component):
    _name = 'prestashop.account.tax.group.match.importer'
    _inherit = 'prestashop.match.importer'
    _apply_on = 'prestashop.account.tax.group'
    _erp_field = 'name'  # prestashop_bind_ids
    _ps_field = 'name'

    def compare_function(self, ps_val, erp_val, ps_dict, erp_dict):
        if ps_val == erp_val:
            return True
        return False


class AccountTaxGroupBatchMatchImporter(Component):
    _name = 'prestashop.account.tax.group.batch.match.importer'
    _inherit = 'prestashop.batch.match.importer'
    _apply_on = 'prestashop.account.tax.group'
