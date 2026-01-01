# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
from odoo.addons.queue_job.job import identity_exact


from odoo import models
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create

_logger = logging.getLogger(__name__)
try:
    from prestapyt import PrestaShopWebServiceError
except ImportError:
    _logger.debug("Cannot import from `prestapyt`")


class ProductCombinationImporter(Component):
    _name = "prestashop.product.product.importer"
    _inherit = "prestashop.importer"
    _apply_on = "prestashop.product.product"

    def _import_dependencies(self):
        record = self.prestashop_record
        if int(record['id_product']):
            self._import_dependency(record['id_product'],
                                    'prestashop.product.template')
        ps_key = self.backend_record.get_version_ps_key('product_option_value')
        option_values = record.get('associations', {}).get(
            'product_option_values', {}).get(ps_key, [])
        if not isinstance(option_values, list):
            option_values = [option_values]
        #         backend_adapter = self.component(
        #             usage='backend.adapter',
        #             model_name='prestashop.product.attribute.value')
        for option_value in option_values:
            #             option_value = backend_adapter.read(option_value['id'])
            #             self._import_dependency(
            #                 option_value['id_attribute_group'],
            #                 'prestashop.product.attribute')
            self._import_dependency(
                option_value['id'],
                'prestashop.product.attribute.value')

    def _after_import(self, binding):
        res = super()._after_import(binding)
        self.import_supplierinfo(binding)
        return res

    def import_supplierinfo(self, binding):
        ps_data = self._get_prestashop_data()
        ps_id = ps_data['id']
        template_ps_id = ps_data['id_product']
        filters = {
            'filter[id_product]': template_ps_id,
            'filter[id_product_attribute]': ps_id
        }
        self.env['prestashop.product.supplierinfo'].with_delay(
            priority=10,
            description=f"Prepare Batch match import prestashop.product.supplierinfo with filters {filters}",
            identity_key=identity_exact
        ).import_batch_merge(
            self.backend_record,
            filters=filters
        )

    def _import(self, binding, **kwargs):
        # We need to pass the template presta record because we need it
        # for combination mapper
        if not hasattr(self.work, "parent_presta_record"):
            tmpl_adapter = self.component(
                usage="backend.adapter", model_name="prestashop.product.template"
            )
            tmpl_record = tmpl_adapter.read(self.prestashop_record.get("id_product"))
            self.work.parent_presta_record = tmpl_record
            if "parent_presta_record" not in self.work._propagate_kwargs:
                self.work._propagate_kwargs.append("parent_presta_record")
        return super()._import(binding, **kwargs)


class ProductCombinationMapper(Component):
    _name = "prestashop.product.product.import.mapper"
    _inherit = "prestashop.import.mapper"
    _apply_on = "prestashop.product.product"

    direct = [
        ('reference', 'reference'),
        ('upc', 'upc'),
    ]

    from_main = []

    @mapping
    def weight(self, record):
        combination_weight = float(record.get("weight", "0.0"))
        # main_weight = float(self.work.parent_presta_record.get("weight", 0.0))
        if not hasattr(self.work, "parent_presta_record"):
            template = self.get_main_template_binding(record)
            main_weight = template.weight
        else:
            main_weight = float(self.work.parent_presta_record.get("weight", 0.0))
        weight = main_weight + combination_weight
        return {"weight": weight}

    @mapping
    def map_boolean_fields(self, record):
        map_values = {'0': False,
                      '1': True}
        return {'default_on': map_values[record.get('default_on', '0') or '0'],
                }

    @mapping
    def product_tmpl_id(self, record):
        template = self.get_main_template_binding(record)
        product_binder = self.binder_for("prestashop.product.product")
        product = product_binder.to_internal(record["id"])
        if not product or product.product_tmpl_id.id != template.odoo_id.id:
            return {"product_tmpl_id": template.odoo_id.id}
        return {}

    # @mapping
    # def from_main_template(self, record):
    #     main_template = self.get_main_template_binding(record)
    #     result = {}
    #     for attribute in self.from_main:
    #         if attribute not in main_template:
    #             continue
    #         if hasattr(main_template[attribute], 'id'):
    #             result[attribute] = main_template[attribute].id
    #         elif isinstance(main_template[attribute], models.BaseModel):
    #             ids = []
    #             for element in main_template[attribute]:
    #                 ids.append(element.id)
    #             result[attribute] = [(6, 0, ids)]
    #         else:
    #             result[attribute] = main_template[attribute]
    #     return result

    def get_main_template_binding(self, record):
        template_binder = self.binder_for('prestashop.product.template')
        return template_binder.to_internal(record['id_product'])

    def _get_option_value(self, record):
        option_values = (
            record.get("associations", {})
            .get("product_option_values", {})
            .get(self.backend_record.get_version_ps_key("product_option_value"), [])
        )
        template_binding = self.get_main_template_binding(record)
        template = template_binding.odoo_id
        if isinstance(option_values, dict):
            option_values = [option_values]
        tmpl_values = template.attribute_line_ids.mapped("product_template_value_ids")
        for option_value in option_values:
            option_value_binder = self.binder_for(
                'prestashop.product.attribute.value')
            option_value_binding = option_value_binder.to_internal(
                option_value['id']
            )
            tmpl_value = tmpl_values.filtered(
                lambda v: v.product_attribute_value_id.id == option_value_binding.odoo_id.id
            )
            assert option_value_binding, "must have a binding for the option"
            yield tmpl_value

    @mapping
    def product_template_attribute_value_ids(self, record):  # should reconsider it
        results = []
        for tmpl_attr_value in self._get_option_value(record):
            results.append(tmpl_attr_value.id)
        return {"product_template_attribute_value_ids": [(6, 0, results)]}

    @mapping
    def main_template_id(self, record):
        template_binding = self.get_main_template_binding(record)
        return {"main_template_id": template_binding.id}

    def _product_code_exists(self, code):
        model = self.env['product.product']
        combination_binder = self.binder_for('prestashop.product.product')
        product = model.with_context(active_test=False).search([
            ('default_code', '=', code),
            ('company_id', '=', self.backend_record.company_id.id),
        ], limit=1)
        return product  # and not combination_binder.to_external(

    #             template_ids, wrap=True)

    @only_create
    @mapping
    def ps_default_code(self, record):
        code = record.get(self.backend_record.product_merge_based_on)
        if not code:
            template = self.get_main_template_binding(record)
            if len(template.odoo_id.product_variant_ids) == 1:
                code = template.odoo_id.ps_default_code
        if not code:
            code = "%s_%s" % (record['id_product'], record['id'])
        res = {'ps_default_code': code}
        return res

    @mapping
    def default_code(self, record):
        code = record.get('reference')
        res = {}
        if not code:
            template = self.get_main_template_binding(record)
            if len(template.odoo_id.product_variant_ids) == 1:
                code = template.odoo_id.ps_default_code
        if not code:
            code = "%s_%s" % (record['id_product'], record['id'])
        if not self._product_code_exists(code):
            res.update({'default_code': code})
            return res
        i = 1
        current_code = '%s_%s' % (code, i)
        while self._product_code_exists(current_code):
            i += 1
            current_code = '%s_%s' % (code, i)
        res.update({'default_code': current_code})
        return res

    @mapping
    def barcode(self, record):
        barcode = record.get("barcode") or record.get("ean13")
        # check_ean = self.env["barcode.nomenclature"].check_ean
        #TODO no check_ean in v18
        if barcode in ["", "0"]:
            backend_adapter = self.component(
                usage="backend.adapter", model_name="prestashop.product.template"
            )
            template = backend_adapter.read(record["id_product"])
            barcode = template.get("barcode") or template.get("ean13")
        if barcode and barcode != "0": # and check_ean(barcode):
            return {"barcode": barcode}
        return {}

    def _get_tax_ids(self, record):
        product_tmpl_adapter = self.component(
            usage="backend.adapter", model_name="prestashop.product.template"
        )
        product_ps = product_tmpl_adapter.read(record["id_product"])
        tax_group = self.binder_for("prestashop.account.tax.group").to_internal(
            product_ps["id_tax_rules_group"], unwrap=True
        )
        tax_ids = tax_group.tax_ids.filtered(
            lambda x: x.type_tax_use in ['sale'] and x.tax_scope in ['consu',
                                                                             False])
        return tax_ids

    def _apply_taxes(self, tax, price):
        if self.backend_record.taxes_included == tax.price_include:
            return price
        factor_tax = tax.price_include and (1 + tax.amount / 100) or 1.0
        if self.backend_record.taxes_included:
            if not tax.price_include:
                return price / factor_tax
        else:
            if tax.price_include:
                return price * factor_tax

    @mapping
    def specific_price(self, record):
        product = self.binder_for(
            'prestashop.product.product').to_internal(
            record['id'], unwrap=True
        )
        product_template = self.binder_for(
            'prestashop.product.template').to_internal(record['id_product'])
        tax = product.product_tmpl_id.taxes_id[:1] or self._get_tax_ids(record)
        impact = float(self._apply_taxes(tax, float(record['price'] or '0.0')))
        cost_price = float(record['wholesale_price'] or '0.0')
        return {
            'list_price': product_template.list_price,
            'standard_price': cost_price or product_template.wholesale_price,
            'impact_price': impact,
            'price_extra': impact,
        }

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}


class ProductProductBatchImporter(Component):
    _name = "prestashop.product.product.batch.importer"
    _inherit = "prestashop.batch.importer"
    _apply_on = "prestashop.product.product"


class ProductProductMatchImporter(Component):
    _name = 'prestashop.product.product.match.importer'
    _inherit = 'prestashop.match.importer'
    _apply_on = 'prestashop.product.product'
    _erp_field = 'ps_default_code'  # prestashop_bind_ids

    #     _ps_field = 'reference'#added it from the run method

    def _odoo_domain_to_consider(self, ps_dict):
        res = super()._odoo_domain_to_consider(ps_dict)
        template_binder = self.binder_for('prestashop.product.template')
        product_tmpl_id = template_binder.to_internal(ps_dict['id_product'], unwrap=True)
        res += [('product_tmpl_id', '=', product_tmpl_id.id)]
        ps_key = self.backend_record.get_version_ps_key('product_option_value')
        option_values = ps_dict.get('associations', {}).get(
            'product_option_values', {}).get(ps_key, [])
        if not isinstance(option_values, list):
            option_values = [option_values]
        attribute_value_domain = []
        for option_value in option_values:
            option_value_binder = self.binder_for('prestashop.product.attribute.value')
            value_id = option_value_binder.to_internal(
                option_value['id'], unwrap=True
            )
            assert value_id, "binding for option value %s not found. Please sync basedata again" % option_value['id']
            attribute_value_domain += [
                ("product_template_attribute_value_ids.product_attribute_value_id", "=",
                 value_id.id)
            ]
            res += attribute_value_domain
        return res  #

    def _odoo_fields_to_consider(self):
        return super()._odoo_fields_to_consider() + ['product_tmpl_id']

    def compare_function(self, ps_val, erp_val, ps_dict, erp_dict):
        ps_key = self.backend_record.get_version_ps_key('product_option_value')
        option_values = ps_dict.get('associations', {}).get(
            'product_option_values', {}).get(ps_key, [])
        if option_values:
            return True
        return False

    def run(self, record_id, **kwargs):
        self._ps_field = self.backend_record.product_merge_based_on
        return super().run(
            record_id, **kwargs
        )


class ProductProductBatchMatchImporter(Component):
    _name = "prestashop.product.product.batch.match.importer"
    _inherit = "prestashop.batch.match.importer"
    _apply_on = "prestashop.product.product"
