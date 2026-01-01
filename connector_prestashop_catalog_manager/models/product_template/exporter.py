# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import timedelta

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, m2o_to_external

_logger = logging.getLogger(__name__)


class ProductTemplateExporter(Component):
    _name = 'prestashop.product.template.exporter'
    _inherit = 'translation.prestashop.exporter'
    _apply_on = 'prestashop.product.template'

    def _has_to_skip(self, binding=False):
        """ Return True if the export can be skipped """
        if binding.odoo_id.id in self.backend_record.exclude_export_template_ids.ids:
            return "Export not done as the product listed in exclude product list"
        else:
            return super()._has_to_skip(binding=binding)

    def export_categories(self, category):
        if not category:
            return
        ps_categ_obj = self.env['prestashop.product.category']
        position_cat_id = ps_categ_obj.search(
            [], order='position desc', limit=1)
        obj_position = position_cat_id.position + 1
        res = {
            'link_rewrite': self.backend_record.get_slug(category.name),
            'position': obj_position,
        }
        self._export_dependency(
            category,
            'prestashop.product.category', bind_values=res)

    #         binding = ps_categ_obj.with_context(
    #             connector_no_export=True).create(res)
    #         self.backend_record.export_record(
    #             'prestashop.product.category',
    #             binding.id)

    def _parent_length(self, categ):
        if not categ.parent_id:
            return 1
        else:
            return 1 + self._parent_length(categ.parent_id)

    def _export_dependencies(self):
        """ Export the dependencies for the product"""
        super()._export_dependencies()
        self.export_categories(self.binding.prestashop_default_category_id)
        for line in self.binding.attribute_line_ids:
            self._export_dependency(
                line.attribute_id,
                'prestashop.product.attribute')
            for value in line.value_ids:
                self._export_dependency(
                    value, 'prestashop.product.attribute.value')
        for tag in self.binding.prestashop_tag_ids:
            self._export_dependency(
                tag, 'prestashop.product.tag')

    def export_variants(self):
        combination_obj = self.env['prestashop.product.product']

        #         for line in self.binding.ps_attribute_line_ids:
        for product in self.binding.combinations_ids:  # product_variant_ids:
            if not product.product_template_attribute_value_ids:
                continue
            #             combination_ext_id = combination_obj.search([
            #                 ('backend_id', '=', self.backend_record.id),
            #                 ('odoo_id', '=', product.id),
            #             ])
            #             if not combination_ext_id:
            #                 combination_ext_id = combination_obj.with_context(
            #                     connector_no_export=True).create({
            #                         'backend_id': self.backend_record.id,
            #                         'odoo_id': product.id,
            #                         'main_template_id': self.binding_id,
            #                     })
            # If a template has been modified then always update PrestaShop
            # combinations
            identity = product.backend_id.generate_identity_key(product)
            product.with_delay(priority=50, identity_key=identity,
                               description=f"Export {product.odoo_id._name} with ID {product.odoo_id.id}",
                               eta=timedelta(seconds=20)).export_record()




    def update_quantities(self):
        #         if len(self.binding.combinations_ids) == 1:#product_variant_ids
        #             product = self.binding.combinations_ids[0].odoo_id#product_variant_ids
        self.binding.odoo_id.update_prestashop_quantities()

    def _after_export(self):
        self.export_variants()
        self.update_quantities()


class ProductTemplateExportMapper(Component):
    _name = 'prestashop.product.template.export.mapper'
    _inherit = 'translation.prestashop.export.mapper'
    _apply_on = 'prestashop.product.template'

    direct = [
        ('available_for_order', 'available_for_order'),
        ('show_price', 'show_price'),
        ('online_only', 'online_only'),
        # ('weight', 'weight'),
        # ('standard_price', 'wholesale_price'),
        (m2o_to_external('default_shop_id'), 'id_shop_default'),
        ('ps_active', 'active'),
        ('barcode', 'barcode'),  # not in latest ps1.6
        ('barcode', 'ean13'),
        #         ('ps_type','type'),
        ('additional_shipping_cost', 'additional_shipping_cost'),
        ('minimal_quantity', 'minimal_quantity'),
        ('on_sale', 'on_sale'),
        ('low_stock_alert', 'low_stock_alert'),
        #         ('ps_state','state')
        #         (m2o_to_external(
        #             'prestashop_default_category_id'), 'id_category_default'),
    ]
    # handled by base mapping `translatable_fields`
    _translatable_fields = [
        ('ps_name', 'name'),
        ('link_rewrite', 'link_rewrite'),
        ('meta_title', 'meta_title'),
        ('meta_description', 'meta_description'),
        ('meta_keywords', 'meta_keywords'),
        #         ('tags', 'tags'),
        ('available_now', 'available_now'),
        ('available_later', 'available_later'),
        ('description_short_html', 'description_short'),
        ('description_html', 'description'),
    ]

    # @mapping
    # def id_shop_default(self, record):
    #     shop_binder = self.binder_for('prestashop.shop')
    #     ext_shop_id = shop_binder.to_external(
    #         self.env['prestashop.shop'].search([], limit=1), wrap=True)
    #     return {'id_shop_default': ext_shop_id}

    def _get_factor_tax(self, tax):
        return (1 + tax.amount / 100) if tax.price_include else 1.0

    @mapping
    def id_category_default(self, record):
        binder = self.binder_for('prestashop.product.category')
        return {'id_category_default': binder.to_external(record.prestashop_default_category_id, wrap=False)}

    @mapping
    def ps_type_mapping(self, record):
        return {'type': record.ps_type,
                'is_virtual': record.ps_type == 'virtual' and 1 or 0
                }

    @mapping
    def list_price(self, record):
        tax = record.taxes_id and record.taxes_id[0] or record.taxes_id  # or condition will be empty record
        if tax.price_include and tax.amount_type == 'percent':
            # 6 is the rounding precision used by PrestaShop for the
            # tax excluded price.  we can get back a 2 digits tax included
            # price from the 6 digits rounded value
            return {
                'price': str.format('{0:.6f}', record.list_price / self._get_factor_tax(tax)),
            }
        else:
            return {'price': str.format('{0:.6f}', record.list_price)}

    @mapping
    def weight(self, record):
        return {'weight': str.format('{0:.6f}', record.weight)}

    @mapping
    def wholesale_price(self, record):
        return {'wholesale_price': str.format('{0:.6f}', record.standard_price)}

    @mapping
    def reference(self, record):
        res = {}
        for f in ['reference', 'upc']:
            if f == self.backend_record.product_merge_based_on:
                res[f] = record.ps_default_code or ''
            else:
                res[f] = getattr(record, f, '') or ''

        return res

    @mapping
    def ps_state(self, record):
        res = {'state': record.ps_state and 1 or 0}
        return res

    #                 'id_shop_group':1,
    # #                 'id_shop':'all',
    #                 'pack_stock_type':3#dont know what it is .its default value is 3
    #                 }

    def _get_product_category(self, record):
        ext_categ_ids = []
        binder = self.binder_for('prestashop.product.category')
        for category in record.prestashop_categ_ids:
            ext_categ_ids.append(
                {'id': binder.to_external(category, wrap=False)})
        return ext_categ_ids


    def _get_product_tags(self, record):
        tag_binder = self.binder_for('prestashop.product.tag')
        ext_tag_ids = []
        for tag in record.prestashop_tag_ids:
            ext_tag_data = {
                'id': tag_binder.to_external(tag.id, False),
            }
            ext_tag_ids.append(ext_tag_data)
        return ext_tag_ids

    def association_items(self, record):
        res = dict()
        res.update({
            'categories': {
                'category': self._get_product_category(record)},
        })
        if record.tag_ids:
            res.update({'tags': {
                self.backend_record.get_version_ps_key('tags'): self._get_product_tags(
                    record)
            }})

        return res

    @mapping
    def associations(self, record):
        res = {
            'associations': {}
            }
        res['associations'].update(self.association_items(record))
        return res

    @mapping
    def tax_ids(self, record):
        if not record.taxes_id:
            return
        binder = self.binder_for('prestashop.account.tax.group')
        ext_id = binder.to_external(record.taxes_id[:1].tax_group_id, wrap=True)
        return {'id_tax_rules_group': ext_id}

    @mapping
    def available_date(self, record):
        if record.available_date:
            return {'available_date': record.available_date.strftime('%Y-%m-%d')}
        return {}

    @mapping
    def date_add(self, record):
        # When export a record the date_add in PS is null.
        return {'date_add': record.ps_active_date and record.ps_active_date.strftime(
            '%Y-%m-%d') or (record.date_add and record.date_add.strftime('%Y-%m-%d')) or
                            record.create_date.strftime('%Y-%m-%d')}

