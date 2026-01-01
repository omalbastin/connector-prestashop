# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models

from odoo.addons.component.core import Component


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    prestashop_groups_bind_ids = fields.One2many(
        comodel_name='prestashop.groups.pricelist',
        inverse_name='odoo_id',
        string='PrestaShop user groups',
    )


class PrestashopGroupsPricelist(models.Model):
    _name = 'prestashop.groups.pricelist'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'product.pricelist': 'odoo_id'}
    _description = "prestashop groups"

    odoo_id = fields.Many2one(
        comodel_name='product.pricelist',
        required=True,
        ondelete='cascade',
        string='Odoo Pricelist',
    )


class PricelistAdapter(Component):
    _name = 'prestashop.groups.pricelist.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.groups.pricelist'

    _prestashop_model = 'groups'
    _export_node_name = 'group'


#     def search(self, filters=None):
#         res = self.client.get(self._prestashop_model, options=filters)
#         tags = res[self._prestashop_model]
#         if not tags:
#             return []
#         tags = tags[self._export_node_name]
#         if isinstance(tags, dict):
#             return [tags]
#         return tags
class PricelistBinder(Component):
    _name = 'prestashop.groups.pricelist.binder'
    _inherit = 'prestashop.binder'
    _apply_on = 'prestashop.groups.pricelist'
