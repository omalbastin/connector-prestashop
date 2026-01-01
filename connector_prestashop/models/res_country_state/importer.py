# © 2016-TODAY Omal Bastin(Steigend IT Solutions) <omalbastin@steigendit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class ResCountryStateImportMapper(Component):
    _name = "prestashop.res.country.state.import.mapper"
    _inherit = "prestashop.import.mapper"
    _apply_on = "prestashop.res.country.state"

    direct = [
        ("name", "name"),
        ("iso_code", "code"),
        #         (external_to_m2o('id_country'), 'country_id'),
    ]

    @mapping
    def country(self, record):
        binder = self.binder_for("prestashop.res.country")
        country = binder.to_internal(record["id_country"], unwrap=True)
        return {"country_id": country.id}


class ResCountryStateImporter(Component):
    _name = "prestashop.res.country.state.importer"
    _inherit = "prestashop.importer"
    _apply_on = "prestashop.res.country.state"


class ResCountryStateMatchImporter(Component):
    _name = "prestashop.res.country.state.match.importer"
    _inherit = "prestashop.match.importer"
    _apply_on = "prestashop.res.country.state"

    _erp_field = "code"
    _ps_field = "iso_code"

    #     _create_binding = False
    _update_with_ps_values = False

    def compare_function(self, ext_val, erp_val, ext_dict, erp_dict):
        if erp_val and ext_val and erp_val.lower() == ext_val.lower():
            return True
        return False

    def _odoo_domain_to_consider(self, ext_dict):
        res = super()._odoo_domain_to_consider(ext_dict)
        country_binder = self.binder_for("prestashop.res.country")
        country_id = country_binder.to_internal(ext_dict["id_country"], unwrap=True)
        res += [("country_id", "=", country_id.id)]
        return res  #


class ResCountryStateBatchMatchImporter(Component):
    _name = "prestashop.res.country.state.batch.match.importer"
    _inherit = "prestashop.batch.match.importer"
    _apply_on = "prestashop.res.country.state"

#     _use_job_queue = False
