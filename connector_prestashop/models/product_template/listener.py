# © 2016-TODAY Omal Bastin(O4 ODOO) <omalbastin@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if

_logger = logging.getLogger(__name__)


class PrestashopProductQuantityListener(Component):
    _name = 'prestashop.product.quantity.listener'
    _inherit = 'prestashop.connector.listener'
    _apply_on = ['prestashop.product.product',
                 'prestashop.product.template']

    def _get_inventory_fields(self):
        # fields which should not trigger an export of the products
        # but an export of their inventory
        return ('quantity', 'out_of_stock')

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        inventory_fields = list(
            set(fields).intersection(self._get_inventory_fields())
        )
        if inventory_fields and record.backend_id.auto_update_stock:
            record.with_delay(priority=20).export_inventory(fields=inventory_fields)
