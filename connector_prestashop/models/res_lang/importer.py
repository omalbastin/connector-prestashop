# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component


class ResLangMatchImporter(Component):
    _name = 'prestashop.res.lang.match.importer'
    _inherit = 'prestashop.match.importer'
    _apply_on = 'prestashop.res.lang'

    _erp_field = 'code'
    _ps_field = 'language_code'
    _copy_fields = [
        ('active', 'active'),
    ]
    _create_match_bind_only = True
    _update_with_ps_values = False
    _consider_inactive_records = False

    def compare_function(self, ps_val, erp_val, ps_dict, erp_dict):
        if len(erp_val.split("_")) == 2 and len(ps_val.split("-")) == 2:
            ps_val_lang, ps_val_country = ps_val.split("-")
            erp_val_lang, erp_val_country = erp_val.split("_")
            if (
                    len(ps_val_lang) == 2
                    and len(erp_val_lang) == 2
                    and ps_val_lang.lower() == erp_val_lang.lower()
                    and len(ps_val_country) == 2
                    and len(erp_val_country) == 2
                    and ps_val_country.lower() == erp_val_country.lower()
            ):
                return True
        elif (
                len(erp_val) >= 2
                and len(ps_val) >= 2
                and erp_val[0:2].lower() == ps_val[0:2].lower()
            ):
            return True
        return False


class ResLangBatchMatchImporter(Component):
    _name = 'prestashop.res.lang.batch.match.importer'
    _inherit = 'prestashop.batch.match.importer'
    _apply_on = 'prestashop.res.lang'

    _use_job_queue = False


class ResLangImporter(Component):
    _name = 'prestashop.res.lang.importer'
    _inherit = 'prestashop.importer'
    _apply_on = 'prestashop.res.lang'
