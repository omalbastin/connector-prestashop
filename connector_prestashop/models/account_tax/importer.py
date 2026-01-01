# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component


class AccountTaxImporter(Component):
    _name = 'prestashop.account.tax.importer'
    _inherit = 'prestashop.importer'
    _apply_on = 'prestashop.account.tax'


class AccountTaxMatchImporter(Component):
    _name = 'prestashop.account.tax.match.importer'
    _inherit = 'prestashop.match.importer'
    _apply_on = 'prestashop.account.tax'

    _erp_field = 'amount'
    _ps_field = 'rate'
    _create_match_bind_only = True
    _update_with_ps_values = False

    def _odoo_fields_to_consider(self):
        return super()._odoo_fields_to_consider() + [
            "price_include",
            "type_tax_use",
            "tax_scope",
            "amount_type",
            "company_id",
        ]

    def compare_function(self, ps_val, erp_val, ps_dict, erp_dict):
        if self.backend_record.taxes_included and erp_dict['price_include']:
            taxes_inclusion_test = True
        else:
            taxes_inclusion_test = not erp_dict['price_include']
        if not taxes_inclusion_test:
            return False
        return (erp_dict['type_tax_use'] == 'sale'
                and erp_dict["tax_scope"] in ["consu", False]
                and erp_dict['amount_type'] == 'percent'
                and abs(erp_val - float(ps_val)) < 0.01
                and self.backend_record.company_id.id == erp_dict['company_id'][0])


class AccountTaxBatchMatchImporter(Component):
    _name = 'prestashop.account.tax.batch.match.importer'
    _inherit = 'prestashop.batch.match.importer'
    _apply_on = 'prestashop.account.tax'

    _use_job_queue = False
