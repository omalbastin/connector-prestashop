# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

# from collections import defaultdict

import logging

from odoo import fields, models
from odoo.addons.component.core import Component

# from odoo.tools.translate import html_translate

_logger = logging.getLogger(__name__)


# try:
#     from odoo.addons.connector_prestashop.prestapyt import PrestaShopWebServiceDict
# except:
#     _logger.debug('Cannot import from `prestapyt`')

class ProductTags(models.Model):
    _inherit = "product.tag"

    name = fields.Char('Name', required=True)
    prestashop_bind_ids = fields.One2many(
        comodel_name="prestashop.product.tag",
        inverse_name="odoo_id",
        string="PrestaShop Bindings",
    )


class PrestashopProductTags(models.Model):
    _name = "prestashop.product.tag"
    _inherit = "prestashop.binding.odoo"
    _inherits = {"product.tag": "odoo_id"}
    _description = "prestashop tags"

    odoo_id = fields.Many2one(
        comodel_name="product.tag",
        string="ODOO ID",
        required=True,
        ondelete='cascade',
    )

    ps_lang_id = fields.Integer('Prestashop Lang ID', default=1)


class PrestashopProductTagsAdapter(Component):
    _name = "prestashop.product.tag.adapter"
    _inherit = "prestashop.adapter"
    _apply_on = "prestashop.product.tag"
    _prestashop_model = "tags"
    _export_node_name = _export_node_name_res = "tag"


#     def search(self, filters=None):
#         res = self.client.get(self._prestashop_model, options=filters)
#         tags = res[self._prestashop_model]
#         if not tags:
#             return []
#         tags = tags[self._export_node_name]
#         if isinstance(tags, dict):
#             return [tags]
#         return tags


class PrestashopProductTagsBinder(Component):
    _name = "prestashop.product.tag.binder"
    _inherit = "prestashop.binder"
    _apply_on = "prestashop.product.tag"
