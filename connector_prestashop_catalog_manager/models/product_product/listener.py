# © 2016-TODAY Omal Bastin(O4 ODOO) <omalbastin@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if

_logger = logging.getLogger(__name__)


class ProductProductListener(Component):
    _name = 'product.product.listener'
    _inherit = 'prestashop.connector.listener'
    _apply_on = 'product.product'

    def _get_product_exclude_fields(self):
        return ['sale_ok', 'prestashop_bind_ids', 'stock_ad', 'stock_st', 'stock_updated']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if not record.product_variant_count:
            return
        fields = list(set(fields).difference(set(self._get_product_exclude_fields())))
        #     if 'active' in fields and not fields['active']:
        #         prestashop_product_combination_unlink(env, record_id)
        #         return
        if fields:
            for binding in record.prestashop_bind_ids:
                priority = 20
                if 'default_on' in fields and fields['default_on']:
                    # PS has to uncheck actual default combination first
                    priority = 99
                identity = binding.backend_id.generate_identity_key(binding)
                binding.with_delay(priority=priority,
                                   description=f"Export {binding.odoo_id._name} with ID {binding.odoo_id.id}",
                                   identity_key=identity).export_record(
                    fields=fields
                )

#TODO create and unlink
# def prestashop_product_combination_unlink(env, record_id):
#     # binding is deactivate when deactive a product variant
#     ps_binding_product = env['prestashop.product.product'].search([
#         ('active', '=', False),
#         ('odoo_id', '=', record_id)
#     ])
#     for binding in ps_binding_product:
#         resource = 'combinations/%s' % (binding.prestashop_id)
#         binding.backend_id.delay().export_delete_record(
#             'prestashop.product.product',
#             binding.prestashop_id, resource)
#     ps_binding_product.unlink()