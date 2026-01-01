# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component


class ProductCategoryDelete(Component):
    _name = 'prestashop.product.category.deleter'
    _inherit = 'prestashop.deleter'
    _apply_on = 'prestashop.product.category'

#     def delete(self, id):
#         """ Delete a record on the external system """
#         return self._call('%s.delete' % self._prestashop_model, [int(id)])
