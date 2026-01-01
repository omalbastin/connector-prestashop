# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.shop',
        inverse_name='odoo_id',
        readonly=True,
        string='PrestaShop Bindings',
    )
