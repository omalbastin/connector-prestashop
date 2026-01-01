# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

_logger = logging.getLogger(__name__)


# try:
#     from odoo.addons.connector_prestashop.prestapyt import PrestaShopWebServiceError
# except:
#     _logger.debug('Cannot import from `prestapyt`')

class SupplierMapper(Component):
    _name = 'prestashop.supplier.mapper'
    _inherit = 'prestashop.import.mapper'

    direct = [
        ('name', 'name'),
        #         ('id', 'prestashop_id'),
        ('active', 'active'),
    ]

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def supplier(self, record):
        return {
            'supplier': True,
            'is_company': True,
            'customer': False,
        }


class SupplierImporter(Component):
    """ Import one simple record """
    _name = 'prestashop.supplier.importer'
    _inherit = 'prestashop.importer'
    _apply_on = 'prestashop.supplier'

    # def _create(self, record):
    #     try:
    #         return super()._create(record)
    #     except ZeroDivisionError:
    #         del record['image']
    #         return super()._create(record)

    def _after_import(self, binding):
        super()._after_import(binding)
        binder = self.binder_for()
        ps_id = binder.to_external(binding)
        filters = {"filter[id_supplier]": "%d" % ps_id}
        self.env["prestashop.product.supplierinfo"].with_delay(
            description=f"Prepare Batch match import prestashop.product.supplierinfo with filters {filters}",
        ).import_batch(
            self.backend_record,
            filters=filters,
        )


class SupplierBatchImporter(Component):
    _name = 'prestashop.supplier.batch.importer'
    _inherit = 'prestashop.batch.importer'
    _apply_on = 'prestashop.supplier'


class SupplierMatchImporter(Component):
    _name = 'prestashop.supplier.match.importer'
    _inherit = 'prestashop.match.importer'
    _apply_on = 'prestashop.supplier'
    _erp_field = 'name'
    _ps_field = 'name'

    #     _default_fields = [(external_to_m2o('id_shop_group'), 'shop_group_id'),]
    #
    def compare_function(self, ps_val, erp_val, ps_dict, erp_dict):
        if not ps_val and not erp_val:
            return False
        if ps_val == erp_val:
            #             erp_model_name = self.model._inherits.iterkeys().next()
            #             model = self.env[erp_model_name].with_context(active_test=False)
            #             erp_record = model.browse(erp_dict['id'])
            #             for ps_record in erp_record.prestashop_bind_ids.filtered(lambda x:x.backend_id.id == self.backend_record.id):
            #                 if ps_dict['id'] != ps_record.prestashop_id:
            #                     return False
            return True
        return False


class SupplierMatchBatchImporter(Component):
    _name = 'prestashop.supplier.match.batch.importer'
    _inherit = 'prestashop.batch.match.importer'
    _apply_on = 'prestashop.supplier'


class SupplierInfoMapper(Component):
    _name = 'prestashop.product.supplierinfo.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.product.supplierinfo'

    direct = [
        ('product_supplier_reference', 'product_code'),
        ('product_supplier_price_te', 'price'),
    ]

    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def partner_id(self, record):
        binder = self.binder_for("prestashop.supplier")
        partner = binder.to_internal(record["id_supplier"], unwrap=True)
        return {"partner_id": partner.id}

    @mapping
    def product_id(self, record):
        if record['id_product_attribute'] != '0':
            binder = self.binder_for('prestashop.product.product')
            product = binder.to_internal(
                record['id_product_attribute'],
                unwrap=True,
            )
            return {'product_id': product.id}
        return {}

    @mapping
    def product_tmpl_id(self, record):
        binder = self.binder_for('prestashop.product.template')
        template = binder.to_internal(record['id_product'], unwrap=True)
        return {'product_tmpl_id': template.id}

    @mapping
    def currency_id(self, record):
        binder = self.binder_for("prestashop.res.currency")
        currency = binder.to_internal(record["id_currency"], unwrap=True)
        # Fallback on supplier currency
        if not currency:
            supplier_binder = self.binder_for("prestashop.supplier")
            supplier = supplier_binder.to_internal(record["id_supplier"], unwrap=True)
            currency = supplier.property_purchase_currency_id
        # fallback on company currency
        if not currency:
            currency = self.backend_record.company_id.currency_id
        return {"currency_id": currency.id}

    @mapping
    def required(self, record):
        return {'min_qty': 0.0, 'delay': 1,
                #                 'product_code':record['product_supplier_reference'],
                #                 'price':record['product_supplier_price_te']
                }

    @mapping
    def sequence(self, record):
        # In case of variants, we have sometime one supplier info by variant
        # and one dummy supplierinfo with no variant. We put a lower sequence
        # on no variant supplier info so the _select_seller system takes
        # first the one which has variants set
        if record["id_product_attribute"] != "0":
            sequence = 5
        else:
            sequence = 50
        return {"sequence": sequence}


class SupplierInfoImporter(Component):
    _name = 'prestashop.product.supplierinfo.importer'
    _inherit = 'prestashop.importer'
    _apply_on = 'prestashop.product.supplierinfo'

    def _import_dependencies(self):
        record = self.prestashop_record
        #         try:
        self._import_dependency(
            record['id_supplier'], 'prestashop.supplier'
        )
        self._import_dependency(
            record['id_product'], 'prestashop.product.template'
        )

        if record['id_product_attribute'] != '0':
            self._import_dependency(
                record['id_product_attribute'],
                'prestashop.product.product'
            )


#         except PrestaShopWebServiceError:
#             raise FailedJobError('Error fetching a dependency')

class SupplierInfoBatchImporter(Component):
    _name = 'prestashop.product.supplierinfo.batch.importer'
    _inherit = 'prestashop.batch.importer'
    _apply_on = 'prestashop.product.supplierinfo'


class SupplierInfoMatchImporter(Component):
    _name = 'prestashop.product.supplierinfo.match.importer'
    _inherit = 'prestashop.match.importer'
    _apply_on = 'prestashop.product.supplierinfo'

    def _odoo_fields_to_consider(self):
        return super()._odoo_fields_to_consider() + ['product_tmpl_id', 'name']

    def _odoo_domain_to_consider(self, ext_dict):
        res = super()._odoo_domain_to_consider(ext_dict)
        supplier_id = ext_dict.get("id_supplier", False)
        supplier_binder = self.binder_for("prestashop.supplier")
        partner = supplier_binder.to_internal(supplier_id, unwrap=True)
        template_id = ext_dict.get("id_product", False)
        template_binder = self.binder_for("prestashop.product.template")
        template = template_binder.to_internal(template_id, unwrap=True)
        res += [("partner_id", "=", partner.id), ("product_tmpl_id", "=", template.id)]
        if ext_dict["id_product_attribute"] != "0":
            product_binder = self.binder_for("prestashop.product.product")
            product = product_binder.to_internal(
                ext_dict['id_product_attribute'],
                unwrap=True,
            )
            res += [('product_id', '=', product.id)]
        return res

    def compare_function(self, ps_val, erp_val, ps_dict, erp_dict):
        supplier_id = ps_dict.get('id_supplier', False)
        template_id = ps_dict.get('id_product', False)
        if supplier_id and template_id:
            return True
        return False


class SupplierInfoMatchBatchImporter(Component):
    _name = 'prestashop.product.supplierinfo.match.batchimporter'
    _inherit = 'prestashop.batch.match.importer'
    _apply_on = 'prestashop.product.supplierinfo'
