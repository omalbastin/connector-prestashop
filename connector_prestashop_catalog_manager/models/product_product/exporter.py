# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import OrderedDict

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

_logger = logging.getLogger(__name__)


class ProductCombinationExport(Component):
    _name = 'prestashop.product.product.exporter'
    _inherit = 'translation.prestashop.exporter'
    _apply_on = 'prestashop.product.product'

    #     def _create(self, record):
    #         """
    #         :param record: browse record to create in prestashop
    #         :return integer: Prestashop record id
    #         """
    #         res = super(ProductCombinationExport, self)._create(record)
    #         return res['prestashop']['combination']['id']

    # def _export_images(self):
    #     if self.binding.image_ids:
    #         image_binder = self.binder_for('prestashop.product.image')
    #         for image_line in self.binding.image_ids:
    #             self._export_dependency(
    #                 image_line,
    #                 'prestashop.product.image')

    def _export_dependencies(self):
        """ Export the dependencies for the product"""
        # TODO add export of category
        attribute_binder = self.binder_for(
            'prestashop.product.attribute')
        option_binder = self.binder_for(
            'prestashop.product.attribute.value')
        for value in self.binding.product_template_attribute_value_ids:
            #             attribute_ext_id = attribute_binder.to_external(
            #                 value.attribute_id.id, wrap=True)
            #             if not attribute_ext_id:
            attribute_binding = self._export_dependency(
                value.attribute_id,
                'prestashop.product.attribute')

            self._export_dependency(
                value,
                'prestashop.product.attribute.value',
                bind_values={'id_attribute_group': attribute_binding.id})

        # if self.backend_record.import_export_images in ['export', 'import_export']:
        #     self._export_images()

    def update_quantities(self):
        self.binding.odoo_id.with_context(
            self.env.context).update_prestashop_qty()

    def _after_export(self):
        self.update_quantities()


class ProductCombinationExportMapper(Component):
    _name = 'prestashop.product.product.export.mapper'
    _inherit = 'translation.prestashop.export.mapper'
    _apply_on = 'prestashop.product.product'

    direct = [
        #         ('default_code', 'reference'),
        ('active', 'active'),
        ('barcode', 'ean13'),
        ('minimal_quantity', 'minimal_quantity'),
        ('weight', 'weight'),
        ('low_stock_alert', 'low_stock_alert'),
    ]

    def _get_factor_tax(self, tax):
        factor_tax = tax.price_include and (1 + tax.amount / 100) or 1.0
        return factor_tax

    @mapping
    def combination_default(self, record):
        return {'default_on': int(record['default_on'])}

    def get_main_template_id(self, record):
        template_binder = self.binder_for('prestashop.product.template')
        return template_binder.to_external(record.main_template_id.id)

    @mapping
    def main_template_id(self, record):
        return {'id_product': self.get_main_template_id(record)}

    @mapping
    def _unit_price_impact(self, record):
        tax = record.taxes_id[:1]
        if tax.price_include and tax.amount_type == 'percent':
            # 6 is the rounding precision used by PrestaShop for the
            # tax excluded price.  we can get back a 2 digits tax included
            # price from the 6 digits rounded value
            return {
                'price': round(
                    record.impact_price / self._get_factor_tax(tax), 6)
            }
        else:
            return {'price': record.impact_price}

    @mapping
    def reference(self, record):
        res = {}
        for f in ['reference', 'upc']:
            # if f == self.backend_record.product_merge_based_on:
            #     res[f] = record.ps_default_code or ''
            # else:
            res[f] = getattr(record, f, '') or ''

        return res

    @mapping
    def cost_price(self, record):
        return {'wholesale_price': str.format('{0:.6f}', record.standard_price)}

    def _get_product_option_value(self, record):
        option_value = []
        option_binder = self.binder_for(
            'prestashop.product.attribute.value')
        for value in record.product_template_attribute_value_ids:
            value_ext_id = option_binder.to_external(value.id, wrap=True)
            if value_ext_id:
                option_value.append({'id': value_ext_id})
        return option_value

    # def _get_combination_image(self, record):
    #     images = []
    #     image_binder = self.binder_for('prestashop.product.image')
    #     for image in record.image_ids:
    #         image_ext_id = image_binder.to_external(image.id, wrap=True)
    #         if image_ext_id:
    #             images.append({'id': image_ext_id})
    #     return images

    @mapping
    def associations(self, record):
        associations = OrderedDict([
            ('product_option_values',
             {'product_option_value':
                  self._get_product_option_value(record)}),
            # ('images', {'image': self._get_combination_image(record) or False})
        ])
        return {'associations': associations}
