# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).



from odoo import models, fields, api  # , exceptions, _
from odoo.addons.component.core import Component


class ProductCategory(models.Model):
    _inherit = 'product.category'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.category',
        inverse_name='odoo_id',
        string="PrestaShop Bindings",
    )
    name_translation = fields.Char(string='Name(Translation)', readonly=False, translate=True)

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            self.name_translation = self.name


class PrestashopProductCategory(models.Model):
    _name = 'prestashop.product.category'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'product.category': 'odoo_id'}
    _description = "Product category prestashop bindings: categories"

    odoo_id = fields.Many2one(
        comodel_name='product.category',
        required=True,
        ondelete='cascade',
        string='Product Category',
    )
    default_shop_id = fields.Many2one(comodel_name='prestashop.shop')
    date_add = fields.Datetime(
        string='Created At (on PrestaShop)',
        readonly=True
    )
    date_upd = fields.Datetime(
        string='Updated At (on PrestaShop)',
        readonly=True
    )
    description = fields.Html(translate=True, help="HTML description from PrestaShop")
    link_rewrite = fields.Char(string="Friendly URL", translate=True)
    meta_description = fields.Char(translate=True)
    meta_keywords = fields.Char(translate=True)
    meta_title = fields.Char(translate=True)
    active_ext = fields.Boolean(string='Active in PS', default=True)
    is_root_category = fields.Boolean()
    position = fields.Integer(string='Position')

class ProductCategoryAdapter(Component):
    _name = 'prestashop.product.category.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.product.category'
    _prestashop_model = 'categories'
    _export_node_name = 'category'
    _export_node_name_res = 'category'


class ProductCategoryBinder(Component):
    _name = 'prestashop.product.category.binder'
    _inherit = 'prestashop.binder'
    _apply_on = 'prestashop.product.category'
