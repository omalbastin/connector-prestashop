# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo.addons.component.core import Component


class ProductProductDelete(Component):
    _name = "prestashop.product.product.deleter"
    _inherit = "prestashop.deleter"
    _apply_on = "prestashop.product.product"
