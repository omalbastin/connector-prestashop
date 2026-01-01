# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class PrestashopStockPickingListener(Component):
    _name = 'prestashop.stock.picking.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['stock.picking']

    def on_tracking_number_added(self, record):
        for binding in record.sale_id.prestashop_bind_ids:
            binding.with_delay().export_tracking_number()
