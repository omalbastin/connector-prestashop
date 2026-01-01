# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import datetime
import logging

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import (
    external_to_m2o,
    mapping,
    only_create,
)
from odoo.addons.queue_job.exception import FailedJobError

from odoo import _, fields, tools

_logger = logging.getLogger(__name__)

# try:
#     import html2text
# except ImportError:
#     _logger.debug("Cannot import `html2text`")

try:
    from bs4 import BeautifulSoup
except ImportError:
    _logger.debug("Cannot import `bs4`")

try:
    from prestapyt import PrestaShopWebServiceError
except ImportError:
    _logger.debug("Cannot import from `prestapyt`")

# try:
#     from odoo.addons.connector_prestashop.prestapyt import PrestaShopWebServiceError
# except ImportError:
#     _logger.debug("Cannot import from `prestapyt`")


class TemplateImportMapper(Component):
    _name = 'prestashop.product.template.import.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.product.template'

    direct = [
        # ('weight', 'weight'),
        # ('wholesale_price', 'standard_price'),
        # ('wholesale_price', 'wholesale_price'),
        (external_to_m2o('id_shop_default'), 'default_shop_id'),
        ('link_rewrite', 'link_rewrite'),
        ('reference', 'reference'),
        ('upc', 'upc'),
        # ('available_for_order', 'available_for_order'),
        # ('on_sale', 'on_sale'),
        ("low_stock_threshold", "low_stock_threshold"),
    ]

    # @mapping
    # def default_shop_id(self, record):
    #     return {'default_shop_id': self.env['prestashop.shop'].search([], limit=1).id}

    @mapping
    def standard_price_weight(self, record):
        if self.has_combinations(record):
            return {}
        else:
            return {"standard_price": record.get("wholesale_price", 0.0),
                    "weight": record.get("weight", 0.0)}

    @mapping
    def map_boolean_fields(self, record):
        map_values = {'0': False,
                      '1': True}
        return {'on_sale': map_values[record.get('on_sale', '0')],
                'available_for_order': map_values[record.get('available_for_order', '0')],
                'show_price': map_values[record.get('show_price', '0')],
                'ps_active': map_values[record.get('active', '0')],
                'low_stock_alert': map_values[record.get('low_stock_alert', '0')],
                }

    def _apply_taxes(self, tax, price):
        # if self.backend_record.taxes_included == tax.price_include:
        #     return price
        factor_tax = tax.price_include and (1 + tax.amount / 100) or 1.0
        if self.backend_record.taxes_included:
            if not tax.price_include:
                return price / factor_tax
            else:
                return price * factor_tax
        else:
            if tax.price_include:
                return price * factor_tax
        return price

    @mapping
    @only_create
    def default_list_price(self, record):
        price = 0.0
        tax = self._get_tax_ids(record)
        if record['price'] != '':
            price = float(record['price'])
        price = self._apply_taxes(tax, price)
        return {'list_price': price}

    @mapping
    def list_price(self, record):
        # Needed for managing different prestashops with different price field
        price = 0.0
        tax = self._get_tax_ids(record)
        if record['price'] != '':
            price = float(record['price'])
        price = self._apply_taxes(tax, price)
        return {'list_price': price}

    @mapping
    def tags_to_m2m(self, record):
        associations = record.get('associations', {})
        tags = associations.get('tags', {}).get(
            self.backend_record.get_version_ps_key('tag'), [])

        if not isinstance(tags, list):
            tags = [tags]
        product_tags = self.env["product.tag"].browse()
        binder = self.binder_for("prestashop.product.tag")
        for tag in tags:
            product_tags |= binder.to_internal(
                tag["id"],
                unwrap=True,
            )
        return {"product_tag_ids": [(6, 0, product_tags.ids)]}

    @mapping
    @only_create
    def name(self, record):
        if record['name']:
            return {'name': record['name']}
        return {'name': 'noname'}

    @mapping
    def ps_name(self, record):
        if record['name']:
            return {'ps_name': record['name']}
        return {'ps_name': 'noname'}

    @mapping
    def data_add(self, record):
        if record["date_add"] == "0000-00-00 00:00:00":
            return {"ps_active_date": fields.Datetime.now(),
                    'date_add': fields.Datetime.now(), }
        return {
            "ps_active_date": self.backend_record.to_utc_datetime(record["date_add"]),
            'date_add': self.backend_record.to_utc_datetime(record["date_add"]),
        }

    @mapping
    def date_upd(self, record):
        if record["date_upd"] == "0000-00-00 00:00:00":
            return {"date_upd": fields.Datetime.now()}
        return {"date_upd": self.backend_record.to_utc_datetime(record["date_upd"])}

    def has_combinations(self, record):
        associations = record.get('associations', {})
        combinations = associations.get('combinations', {}).get(
            self.backend_record.get_version_ps_key('combinations'))
        return len(combinations or '') != 0


    def _template_code_exists(self, code):
        model = self.env['product.template']
        template_ids = model.search([
            ('default_code', '=', code),
            "|",
            ("company_id", "=", self.backend_record.company_id.id),
            ("company_id", "=", False),
        ], limit=1)
        return len(template_ids) > 0

    @only_create
    @mapping
    def ps_default_code(self, record):
        code = record.get(self.backend_record.product_merge_based_on)
        if not code:
            code = "%s_%s" % ('-'.join(record['name'].split()), record['id'])
        res = {'ps_default_code': code}
        return res

    @only_create
    @mapping
    def default_code(self, record):
        if self.has_combinations(record):
            return {}
        code = record.get('reference')
        if not code:
            code = "backend_%d_product_%s" % (
                self.backend_record.id, record['id']
            )
        res = {'default_code': code}
        if not self._template_code_exists(code):
            res.update({'default_code': code,})
            return res
        i = 1
        current_code = '%s_%d' % (code, i)
        while self._template_code_exists(current_code):
            i += 1
            current_code = '%s_%d' % (code, i)
        res.update({'default_code': current_code,})
        return res

    def clear_html_field(self, content):
        html = tools.html2plaintext(content)
        return html

    @staticmethod
    def sanitize_html(content):
        content = BeautifulSoup(content, 'html.parser')
        # Prestashop adds both 'lang="fr-ch"' and 'xml:lang="fr-ch"'
        # but Odoo tries to parse the xml for the translation and fails
        # due to the unknow namespace
        for child in content.find_all(lambda tag: tag.has_attr('xml:lang')):
            del child['xml:lang']
        return content.prettify()

    @mapping
    def descriptions(self, record):
        return {
            'description': self.clear_html_field(
                record.get('description_short', '')),
            'description_html': self.sanitize_html(
                record.get('description', '')),
            'description_short_html': self.sanitize_html(
                record.get('description_short', '')),
        }

    @mapping
    def sale_ok(self, record):
        # if this product has combinations, we do not want to sell this
        # product, but its combinations (so sale_ok = False in that case).
        return {'sale_ok': True}

    @mapping
    def purchase_ok(self, record):
        return {'purchase_ok': True}

    def get_categ_ids(self, record):
        categories = record['associations'].get('categories', {}).get(
            self.backend_record.get_version_ps_key('category'), [])
        if not isinstance(categories, list):
            categories = [categories]
        ps_product_categories = self.env['prestashop.product.category'].browse()
        binder = self.binder_for('prestashop.product.category')
        for ps_category in categories:
            ps_product_categories |= binder.to_internal(
                ps_category['id'],
                unwrap=False,
            )
        return ps_product_categories

    @mapping
    @only_create
    def categ_ids(self, record):
        ps_product_categories = self.get_categ_ids(record)
        product_categories = ps_product_categories.mapped('odoo_id')
        return {'categ_ids': [(6, 0, product_categories.ids)]}

    @mapping
    def prestashop_categ_ids(self, record):
        product_categories = self.get_categ_ids(record)
        return {'prestashop_categ_ids': [(6, 0, product_categories.ids)]}

    @mapping
    @only_create
    def default_odoo_category_id(self, record):
        if not int(record['id_category_default']):
            return
        binder = self.binder_for('prestashop.product.category')
        category = binder.to_internal(
            record['id_category_default'],
            unwrap=True,
        )
        if category:
            return {'categ_id': category.id,
                    }

    @mapping
    def default_category_id(self, record):
        if not int(record['id_category_default']):
            return
        binder = self.binder_for('prestashop.product.category')
        category = binder.to_internal(
            record['id_category_default'],
            unwrap=False,
        )
        if category:
            return {
                'prestashop_default_category_id': category.id}

    #TODO do we need to map company. or maybe if its multi company
    @mapping
    def company_id(self, record):
        return {'company_id': self.backend_record.company_id.id}

    @mapping
    def barcode(self, record):
        if self.has_combinations(record):
            return {}
        barcode = record.get('barcode') or record.get('ean13')
        if barcode in ['', '0']:
            return {}
        # if self.env['barcode.nomenclature'].check_ean(barcode):
        #todo check_ean not in v18
        return {'barcode': barcode}
        # return {}

    def _get_tax_ids(self, record):
        # if record['id_tax_rules_group'] == '0':
        #     return {}
        binder = self.binder_for('prestashop.account.tax.group')
        tax_group = binder.to_internal(
            record['id_tax_rules_group'],
            unwrap=True,
        )
        tax_ids = tax_group.tax_ids.filtered(
            lambda x: (x.type_tax_use in ['sale'])
                      and x.tax_scope in ["consu", False])
        if tax_group:
            ERROR = "Tax group `{}` should have one and only one tax, currently have {}"
            assert len(tax_ids) == 1, _(ERROR).format(tax_group.name, len(tax_ids))
        return tax_ids

    @mapping
    def taxes_id(self, record):
        taxes = self._get_tax_ids(record)
        return {'taxes_id': [(6, 0, taxes.ids)]}

    @mapping
    def detailed_type(self, record):
        # If the product has combinations, this main product is not a real
        # product. So it is set to a 'service' kind of product. Should better
        # be a 'virtual' product... but it does not exist...
        # The same if the product is a virtual one in prestashop.
        if record['type']['value'] and record['type']['value'] == 'virtual':
            return {"type": 'consu'}  # service
        return {"type": 'consu', "is_storable": True}

    @mapping
    def ps_type(self, record):
        # If the product has combinations, this main product is not a real
        # product. So it is set to a 'service' kind of product. Should better
        # be a 'virtual' product... but it does not exist...
        # The same if the product is a virtual one in prestashop.
        if record['type']['value']:
            return {"ps_type": record['type']['value']}
        return {"ps_type": 'simple'}

    @mapping
    def visibility(self, record):
        visibility = record.get("visibility")
        if visibility not in ("both", "catalog", "search"):
            visibility = "none"
        return {"visibility": visibility}


class ProductTemplateImporter(Component):
    """ Import one translatable record """
    _name = 'prestashop.product.template.importer'
    _inherit = 'prestashop.translatable.importer'
    _apply_on = 'prestashop.product.template'

    #     _base_mapper = TemplateMapper

    _translatable_fields = [
        'name',
        'description',
        'link_rewrite',
        'description_short',
        'meta_title',
        'meta_description',
        'meta_keywords',
    ]

    def __init__(self, environment):
        """
        :param environment: current environment (backend, session, ...)
        :type environment: :py:class:`connector.connector.ConnectorEnvironment`
        """
        super().__init__(environment)
        self.default_category_error = False

    # def _before_import(self, binding=None):
    #     super()._before_import(binding=binding)
    #     if not binding:
    #         return
    #     binding.with_context(lang=False).write()

    def _after_import(self, binding):
        res = super()._after_import(binding)
        # if self.backend_record.import_export_images in ['import','import_export']:
        #     self.import_images(binding)
        self.attribute_line(binding)

        self.import_combinations()
        # self.import_supplierinfo(binding)
        self.deactivate_default_product(binding)
        self.warning_default_category_missing(binding)
        return res

    def warning_default_category_missing(self, binding):
        if self.default_category_error:
            pass
            # TODO post msg / create activity
            # msg = _('The default category could not be imported.')
            # self.backend_record.add_checkpoint(
            #     binding.odoo_id,
            #     message=msg,
            # )

    def deactivate_default_product(self, binding):
        # don't consider product as having variant if they are inactive.
        # don't try to inactive a product if it is already inactive.
        binding = binding.with_context(active_test=True)
        if binding.product_variant_count == 1:
            return
        for product in binding.product_variant_ids:
            if not product.product_template_attribute_value_ids:
                product.write({'active': False})

    def attribute_line(self, binding):
        record = self.prestashop_record
        template = binding.odoo_id
        attribute_values = {}
        option_value_binder = self.binder_for(
            "prestashop.product.attribute.value"
        )

        ps_key = self.backend_record.get_version_ps_key("product_option_value")
        option_values = (
            record.get("associations", {})
            .get("product_option_values", {})
            .get(ps_key, [])
        )
        if not isinstance(option_values, list):
            option_values = [option_values]

        for option_value in option_values:
            if not option_value["id"]:
                continue
            value = option_value_binder.to_internal(option_value["id"]).odoo_id
            attr_id = value.attribute_id.id
            value_id = value.id
            if attr_id not in attribute_values:
                attribute_values[attr_id] = []
            attribute_values[attr_id].append(value_id)
        remaining_attr_lines = template.with_context(
            active_test=False
        ).attribute_line_ids
        for attr_id, value_ids in attribute_values.items():
            attr_line = template.with_context(
                active_test=False
            ).attribute_line_ids.filtered(lambda al: al.attribute_id.id == attr_id)
            if attr_line:
                values = {"value_ids": list(map(lambda x: (4, x), value_ids))
                          # "active": True
                          }
                if not attr_line.active:
                    values.update({'active': True})
                attr_line.write(values)
                remaining_attr_lines -= attr_line
            else:
                attr_line = self.env["product.template.attribute.line"].create(
                    {
                        "attribute_id": attr_id,
                        "product_tmpl_id": template.id,
                        "value_ids": [(6, 0, value_ids)],
                    }
                )
        # if remaining_attr_lines: # what if this attribute is using for another product for different ps shop
        #     remaining_attr_lines.unlink()

    def _import_combination(self, combination, **kwargs):
        """Import a combination
        Can be overriden for instance to forward arguments to the importer
        """
        # We need to pass the template presta record because we need it
        # for combination mapper
        self.work.parent_presta_record = self.prestashop_record
        if "parent_presta_record" not in self.work._propagate_kwargs:
            self.work._propagate_kwargs.append("parent_presta_record")
        self._import_dependency(
            combination["id"], "prestashop.product.product", always=True,
            with_delay=True, **kwargs
        )

    # def _delay_product_image_variant(self, combinations, **kwargs):
    #     delayable = self.env["prestashop.product.product"].with_delay(priority=15)
    #     delayable.set_product_image_variant(self.backend_record, combinations, **kwargs)

    def import_combinations(self):
        prestashop_record = self._get_prestashop_data()
        associations = prestashop_record.get('associations', {})

        ps_key = self.backend_record.get_version_ps_key('combinations')
        combinations = associations.get('combinations', {}).get(ps_key, [])
        if not isinstance(combinations, list):
            combinations = [combinations]
        if combinations:
            first_exec = combinations.pop(
                combinations.index({
                    'id': prestashop_record[
                        'id_default_combination']['value']}))
            if first_exec:
                # self.env['prestashop.product.combination'].import_record_merge(self.backend_record,
                #                                                                first_exec['id'])
                self._import_combination(first_exec)
            for combination in combinations:
                self._import_combination(combination)
        # if self.backend_record.import_export_images in ['import', 'import_export']:
        #     if combinations and associations['images'].get('image'):
        #         self._delay_product_image_variant([first_exec] + combinations)

    # def import_images(self, binding):
    #     prestashop_record = self._get_prestashop_data()
    #     associations = prestashop_record.get('associations', {})
    #     images = associations.get('images', {}).get(
    #         self.backend_record.get_version_ps_key('image'), {})
    #     if not isinstance(images, list):
    #         images = [images]
    #     for image in images:
    #         if image.get('id'):
    #             self.env['prestashop.product.image'].with_delay(priority=10).import_product_image(
    #                 self.backend_record,
    #                 'products',
    #                 prestashop_record['id'],
    #                 image['id'],
    #             )

    def import_supplierinfo(self, binding):#TODO not using now
        ps_id = self._get_prestashop_data()['id']
        filters = {
            'filter[id_product]': ps_id,
            'filter[id_product_attribute]': 0
        }
        self.env["prestashop.product.supplierinfo"].with_delay().import_batch_merge(
            self.backend_record,
            filters=filters
        )
        ps_product_template = binding
        template_id = ps_product_template.odoo_id.id
        ps_supplierinfos = self.env["prestashop.product.supplierinfo"].search(
            [("product_tmpl_id", "=", template_id)]
        )
        for ps_supplierinfo in ps_supplierinfos:
            try:
                ps_supplierinfo.resync()
            # PrestaShopWebServiceError is transformed in FailedJobError when
            # supplierinfo can't fetch combination dependency. If combination has been
            # removed, we want to clean the supplierinfo too)
            except (PrestaShopWebServiceError, FailedJobError):
                ps_supplierinfo.odoo_id.unlink()

    def _import_dependencies(self):
        self._import_default_category()
        self._import_categories()
        # self._import_manufacturer()
        self._import_tags()

        record = self.prestashop_record
        ps_key = self.backend_record.get_version_ps_key("product_option_value")
        option_values = (
            record.get("associations", {})
            .get("product_option_values", {})
            .get(ps_key, [])
        )
        if not isinstance(option_values, list):
            option_values = [option_values]
        backend_adapter = self.component(
            usage="backend.adapter",
            model_name="prestashop.product.attribute.value",
        )
        #        presta_option_values = []
        for option_value in option_values:
            if not option_value["id"]:
                continue
            option_value_read = backend_adapter.read(option_value["id"])
            self._import_dependency(
                option_value_read["id_attribute_group"],
                "prestashop.product.attribute",
            )
            self._import_dependency(
                option_value_read["id"], "prestashop.product.attribute.value"
            )

    #            presta_option_values.append(option_value)
    #        self.template_attribute_lines(presta_option_values)

    # def _import_manufacturer(self):
    #     self.component(usage="manufacturer.product.importer").import_manufacturer(
    #         self.prestashop_record.get("id_manufacturer")
    #     )

    #     def get_template_model_id(self):
    #         ir_model = self.env['ir.model'].search([
    #             ('model', '=', 'product.template')], limit=1)
    #         assert len(ir_model) == 1
    #         return ir_model.id

    def _import_default_category(self):
        record = self.prestashop_record
        if int(record['id_category_default']):
            #             try:
            self._import_dependency(record['id_category_default'],
                                    'prestashop.product.category')  # ,importer_class=PrestashopImporter

    #             except PrestaShopWebServiceError:
    #                 # a checkpoint will be added in _after_import (because
    #                 # we'll know the binding at this point)
    #                 self.default_category_error = True

    def _import_categories(self):
        record = self.prestashop_record
        associations = record.get('associations', {})
        categories = associations.get('categories', {}).get(
            self.backend_record.get_version_ps_key('category'), [])
        if not isinstance(categories, list):
            categories = [categories]
        for category in categories:
            self._import_dependency(category['id'],
                                    'prestashop.product.category')  # ,importer_class=PrestashopImporter

    def _import_tags(self):
        record = self.prestashop_record
        associations = record.get('associations', {})
        tags = associations.get('tags', {}).get(
            self.backend_record.get_version_ps_key('tag'), [])
        if not isinstance(tags, list):
            tags = [tags]
        for tag in tags:
            self._import_dependency(tag['id'], 'prestashop.product.tag')

    # def _has_to_skip(self, binding=False):
    #     """Return True if the import can be skipped"""
    #     skip = False
    #     if (
    #         self.prestashop_record["active"] == "0"
    #         and self.backend_record.is_skip_product_not_active
    #     ):
    #         skip = True
    #     return skip


class ProductTemplateBatchImporter(Component):
    _name = 'prestashop.product.template.batch.importer'
    _inherit = 'prestashop.batch.importer'
    _apply_on = 'prestashop.product.template'


class ProductTemplateMatchImporter(Component):
    _name = 'prestashop.product.template.match.importer'
    _inherit = 'prestashop.match.importer'
    _apply_on = 'prestashop.product.template'

    _erp_field = 'ps_default_code'  # prestashop_bind_ids

    #     _ps_field = 'reference'#added at run method

    #     def _ps_fields_to_consider(self):
    #         return super(ProductTemplateMergeImporter, self)._ps_fields_to_consider() +['reference']
    #
    def _odoo_fields_to_consider(self):
        res = super()._odoo_fields_to_consider()
        res.append('barcode')
        return res

    def compare_function(self, ps_val, erp_val, ps_dict, erp_dict):
        if not ps_val and not erp_val:
            return False
        if ps_val == erp_val:
            if not ps_dict.get('ean13') or not erp_dict['barcode'] or ps_dict.get('ean13') == erp_dict['barcode']:
                return True
        #         else:
        #             return super(ProductTemplateMergeImporter, self).compare_function(ps_val, erp_val, ps_dict, erp_dict)
        return False

    def run(self, record_id, **kwargs):
        self._ps_field = self.backend_record.product_merge_based_on
        return super().run(record_id, **kwargs
        )


class ProductTemplateBatchMatchImporter(Component):
    _name = 'prestashop.product.template.batch.match.importer'
    _inherit = 'prestashop.batch.match.importer'
    _apply_on = 'prestashop.product.template'


class ProductInventoryBatchImporter(Component):
    _name = '_import_stock_available.batch.importer'
    _inherit = 'prestashop.batch.importer'
    _apply_on = '_import_stock_available'

    def run(self, filters=None, **kwargs):
        if filters is None:
            filters = {}
        filters['display'] = '[id,id_product,id_product_attribute]'
        return super().run(filters, **kwargs)

    def _run_page(self, filters, **kwargs):
        records = self.backend_adapter.get(filters)
        for record in records['stock_availables']['stock_available']:
            # if product has combinations then do not import product stock
            # since combination stocks will be imported
            if record['id_product_attribute'] == '0':
                combination_stock_ids = self.backend_adapter.search({
                    'filter[id_product]': record['id_product'],
                    'filter[id_product_attribute]': '>[0]',
                })
                if combination_stock_ids:
                    continue
            self._import_record(record['id'], record=record, **kwargs)

        return records['stock_availables']['stock_available']

    def _run_page_splitter(self, filters, **kwargs):
        record_ids = self.backend_adapter.get(filters)
        self.env["_import_stock_available"].with_delay(
            description=f"stock batch import with filters {filters}",
            **kwargs).import_batch(filters, **kwargs
                                   )
        return record_ids["stock_availables"]["stock_available"]

    def _import_record(self, record_id, record=None, **kwargs):
        """ Delay the import of the records"""
        assert record
        self.env["_import_stock_available"].with_delay(
            description=f"Stock Import for ps dict {record} with ID {record_id}",
        ).import_record(
            self.backend_record,
            record_id,
            record=record,
            **kwargs
        )


class ProductInventoryImporter(Component):
    _name = '_import_stock_available.importer'
    _inherit = 'prestashop.importer'
    _apply_on = '_import_stock_available'

    def _get_quantity(self, record):
        filters = {
            'filter[id_product]': record['id_product'],
            'filter[id_product_attribute]': record['id_product_attribute'],
            'display': '[quantity]',
        }
        quantities = self.backend_adapter.get(filters)
        all_qty = 0
        quantities = quantities['stock_availables']['stock_available']

        if isinstance(quantities, dict):
            quantities = [quantities]
        for quantity in quantities:
            all_qty += int(quantity['quantity'])
        return all_qty

    def _get_binding(self):
        record = self.prestashop_record
        if record["id_product_attribute"] == "0":
            binder = self.binder_for("prestashop.product.template")
            return binder.to_internal(record["id_product"])
        binder = self.binder_for("prestashop.product.product")
        return binder.to_internal(record["id_product_attribute"])

    def _import_dependencies(self):
        """ Import the dependencies for the record"""
        record = self.prestashop_record
        self._import_dependency(
            record['id_product'], 'prestashop.product.template'
        )
        if record['id_product_attribute'] != '0':
            self._import_dependency(
                record['id_product_attribute'],
                'prestashop.product.product'
            )

    def _check_in_new_connector_env(self):
        # not needed in this importer
        return

    def run(self, prestashop_id, record=None, **kwargs):
        assert record
        self.prestashop_record = record
        return super().run(
            prestashop_id, **kwargs
        )

    def _import(self, binding, **kwargs):
        record = self.prestashop_record
        qty = self._get_quantity(record)
        if qty < 0:
            qty = 0
        if binding._name == 'prestashop.product.template':
            products = binding.odoo_id.product_variant_ids
        else:
            products = binding.odoo_id
        if len(products) > 1 and record['id_product_attribute'] == '0':
            # no need to import stock shown in the product if it have combinations with specific stock
            return "No stock import done"
        location = (self.backend_record.stock_location_id or
                    self.backend_record.warehouse_id.lot_stock_id)
        for product in products:
            vals = {
                'location_id': location.id,
                'product_id': product.id,
                'new_quantity': qty,
            }
            template_qty = self.env['stock.change.product.qty'].create(vals)
            template_qty.with_context(
                active_id=product.id,
                connector_no_export=True,
            ).change_product_qty()
        message = _('Stock Imported for products %s.')
        return message % products
