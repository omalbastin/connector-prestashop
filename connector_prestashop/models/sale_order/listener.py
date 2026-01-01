# © 2016-TODAY Omal Bastin(O4 ODOO) <omalbastin@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if


class SaleOrderListener(Component):
    _name = 'sale.order.listener'
    _inherit = 'prestashop.connector.listener'
    _apply_on = ['sale.order']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if 'ps_order_state_id' not in fields:
            return
        if not record.prestashop_bind_ids:
            return
        for binding in record.prestashop_bind_ids:
            if binding.prestashop_id:
                binding.with_delay(priority=20,
                                   description=f"Export Sale state of {record.display_name}"
                                   ).export_sale_state()
