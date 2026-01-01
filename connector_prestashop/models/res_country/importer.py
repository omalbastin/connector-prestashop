# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component


class ResCountryMatchImporter(Component):
    _name = 'prestashop.res.country.match.importer'
    _inherit = 'prestashop.match.importer'
    _apply_on = 'prestashop.res.country'

    _erp_field = 'code'
    _ps_field = 'iso_code'

    _create_match_bind_only = True
    _update_with_ps_values = False

    def _odoo_fields_to_consider(self):
        res = super()._odoo_fields_to_consider()
        res.append('name')
        return res

    def compare_function(self, ext_val, erp_val, ext_dict, erp_dict):
        if (
                erp_val and
                ext_val and
                erp_val.lower() == ext_val.lower()
        ):
            return True
        return False


class ResCountryBatchMatchImporter(Component):
    _name = 'prestashop.res.country.batch.match.importer'
    _inherit = 'prestashop.batch.match.importer'
    _apply_on = 'prestashop.res.country'


class ResCountryImporter(Component):
    _name = 'prestashop.res.country.importer'
    _inherit = 'prestashop.importer'
    _apply_on = 'prestashop.res.country'
