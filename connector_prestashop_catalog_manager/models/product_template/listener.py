# © 2016-TODAY Omal Bastin(O4 ODOO) <omalbastin@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.addons.component.core import AbstractComponent, Component
from odoo.addons.component_event import skip_if

_logger = logging.getLogger(__name__)


class PrestashopListener(AbstractComponent):
    _inherit = 'prestashop.connector.listener'


class ProductTemplateListener(Component):
    _name = 'product.template.listener'
    _inherit = 'prestashop.connector.listener'
    _apply_on = 'product.template'

    def _get_excluded_tmpl_fields(self):
        # fields which should not trigger an export of the products
        # but an export of their inventory
        return ['default_code', 'sale_ok', 'prestashop_bind_ids',  # 'ps_auto_create',
                'message_follower_ids', 'event_ids',
                'nutrition_line_ids',
                'stock_ad', 'stock_st', 'stock_updated']  # from module nutrion

    def _ps_needed_fields(self):
        direct = ['name', 'available_for_order', 'show_price', 'online_only',
                  'ps_active', 'barcode', 'additional_shipping_cost',
                  'minimal_quantity', 'on_sale', 'low_stock_alert']
        translatable = ['ps_name', 'link_rewrite', 'meta_title', 'meta_description',
                        'meta_keywords', 'available_now', 'available_later',
                        'description_short_html', 'description_html']
        # shop_id
        others = ['prestashop_default_category_id', 'ps_type', 'list_price', 'taxes_id',
                  'weight', 'standard_price', 'reference', 'upc', 'ps_state',
                  'prestashop_categ_ids', 'line_feature_ids', 'prestashop_tag_ids',
                  'available_date', 'date_add']
        return direct + translatable + others

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.with_delay(priority=10).create_ps_records()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):

        if not record.ps_default_code:
            return
        record.with_delay(priority=10).create_ps_records()
        # fields = list(set(fields).difference(set(self._get_excluded_tmpl_fields())))
        triggered = set(fields) & set(self._ps_needed_fields())
        if triggered:
            for binding in record.prestashop_bind_ids:
                identity = binding.backend_id.generate_identity_key(binding)
                binding.with_delay(priority=20,
                                   description=f"Export {binding.odoo_id._name} with ID {binding.odoo_id.id}",
                                   identity_key=identity).export_record(field_names=fields)


class PrestashopProductTemplateListener(Component):
    _name = 'prestashop.product.template.listener'
    _inherit = 'prestashop.connector.listener'
    _apply_on = 'prestashop.product.template'

    # def _get_inventory_fields(self):
    #     # fields which should not trigger an export of the products
    #     # but an export of their inventory
    #     return ('quantity', 'out_of_stock')

    def _get_excluded_tmpl_fields(self):
        # fields which should not trigger an export of the products
        # but an export of their inventory
        return ['default_code', 'sale_ok', 'prestashop_bind_ids',  # 'ps_auto_create',
                'line_feature_ids', 'message_follower_ids', 'event_ids',
                'nutrition_line_ids',
                'stock_ad', 'stock_st', 'stock_updated']  # from module nutrion

    def _ps_needed_fields(self):
        direct = ['name', 'available_for_order', 'show_price', 'online_only',
                  'ps_active', 'barcode', 'additional_shipping_cost',
                  'minimal_quantity', 'on_sale', 'low_stock_alert']
        translatable = ['ps_name', 'link_rewrite', 'meta_title', 'meta_description',
                        'meta_keywords', 'available_now', 'available_later',
                        'description_short_html', 'description_html']
        # shop_id
        others = ['prestashop_default_category_id', 'ps_type', 'list_price', 'taxes_id',
                  'weight', 'standard_price', 'reference', 'upc', 'ps_state',
                  'prestashop_categ_ids', 'line_feature_ids', 'prestashop_tag_ids',
                  'available_date', 'date_add']
        return direct + translatable + others

    @skip_if(lambda self, record, fields, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        identity = record.backend_id.generate_identity_key(record)
        record.with_delay(priority=20,
                          description=f"Export {record.odoo_id._name} with ID {record.odoo_id.id}",
                          identity_key=identity).export_record()

    @skip_if(lambda self, record, fields, **kwargs:
             self.no_connector_export(record) or self.need_to_export(record, fields=fields))
    def on_record_write(self, record, fields=None):
        triggered = set(fields) & set(self._ps_needed_fields())
        if triggered:
            # if fields:
            identity = record.backend_id.generate_identity_key(record)
            record.with_delay(priority=20,
                              description=f"Export {record.odoo_id._name} with ID {record.odoo_id.id}",
                              identity_key=identity).export_record(field_names=fields)
            # Propagate minimal_quantity from template to variants
            if 'minimal_quantity' in fields:
                record.odoo_id.mapped(
                    'product_variant_ids.prestashop_bind_ids').with_context(
                    no_connector_export=True).write({
                    'minimal_quantity': record.minimal_quantity
                })
