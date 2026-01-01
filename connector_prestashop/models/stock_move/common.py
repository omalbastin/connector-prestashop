# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockLocation(models.Model):
    _inherit = 'stock.location'

    prestashop_synchronized = fields.Boolean(
        string='Sync with PrestaShop',
        help='Check this option to synchronize this location with PrestaShop')

    @api.model
    def get_prestashop_stock_locations(self):
        prestashop_locations = self.search(
            [
                # ("prestashop_synchronized", "=", True),
                ("usage", "=", "internal"),
            ]
        )
        return prestashop_locations


# class StockMove(models.Model):
#     _inherit = "stock.move"
#
#     def _action_done(self, cancel_backorder=False):
#         location_obj = self.env['stock.location']
#         ps_locations = location_obj.get_prestashop_stock_locations()
#         res_moves = super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)
#         for move in res_moves:
#             if move.location_id in ps_locations or move.location_dest_id in ps_locations:
#                 move.product_id.product_tmpl_id.with_delay().update_prestashop_quantities()
#         return res_moves


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model_create_multi
    def create(self, vals_list):
        location_obj = self.env['stock.location']
        ps_locations = location_obj.get_prestashop_stock_locations()
        quants = super().create(vals_list)
        for quant in quants:
            if quant.location_id in ps_locations:
                quant.product_id.update_prestashop_qty()
        return quants

    def write(self, vals):
        location_obj = self.env['stock.location']
        ps_locations = location_obj.get_prestashop_stock_locations()
        res = super().write(vals)
        for quant in self:
            location = quant.location_id
            if location in ps_locations:
                # quant.invalidate_cache()
                quant.product_id.update_prestashop_qty()
        return res

    def unlink(self):
        ps_locations = self.env['stock.location']. \
            get_prestashop_stock_locations()
        product_ids = self.filtered(lambda x: x.location_id in ps_locations).mapped('product_id')
        res = super().unlink()
        product_ids.update_prestashop_qty()
        return res
