# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component


class ResCurrencyMatchImporter(Component):
    _name = 'prestashop.res.currency.match.importer'
    _inherit = 'prestashop.match.importer'
    _apply_on = 'prestashop.res.currency'

    _erp_field = 'name'
    _ps_field = 'iso_code'

    _create_match_bind_only = True
    _update_with_ps_values = False

    def compare_function(self, ps_val, erp_val, ps_dict, erp_dict):
        if len(erp_val) == 3 and len(ps_val) == 3 and \
                erp_val[0:3].lower() == ps_val[0:3].lower():
            return True
        return False


class ResCurrencyBatchMatchImporter(Component):
    _name = 'prestashop.res.currency.batch.match.importer'
    _inherit = 'prestashop.batch.match.importer'
    _apply_on = 'prestashop.res.currency'


class ResCurrencyImporter(Component):
    _name = 'prestashop.res.currency.importer'
    _inherit = 'prestashop.importer'
    _apply_on = 'prestashop.res.currency'
