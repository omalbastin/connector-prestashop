# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields
from odoo.addons.component.core import Component


class PrestashopShopGroup(models.Model):
    _name = 'prestashop.shop.group'
    _inherit = 'prestashop.binding'
    #     _inherits = {'shop.group': 'odoo_id'}
    _description = 'PrestaShop Shop Group'

    name = fields.Char('Name', required=True)

    shop_ids = fields.One2many(
        comodel_name='prestashop.shop',
        inverse_name='shop_group_id',
        readonly=True,
        string="Shops",
    )
    company_id = fields.Many2one(
        related='backend_id.company_id',
        comodel_name="res.company",
        string='Company'
    )
    # old_table_id = fields.Integer(string='Old table ID')


class ShopGroupAdapter(Component):
    _name = 'prestashop.shop.group.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.shop.group'
    _prestashop_model = 'shop_groups'


class ShopGroupBinder(Component):
    _name = 'prestashop.shop.group.binder'
    _inherit = 'prestashop.binder'
    _apply_on = 'prestashop.shop.group'


class PrestashopShop(models.Model):
    _name = 'prestashop.shop'
    _inherit = 'prestashop.binding'
    _description = 'PrestaShop Shop'

    # @api.depends('shop_group_id', 'shop_group_id.backend_id')
    # def _compute_backend_id(self):
    #     for shop in self:
    #         shop.backend_id = shop.shop_group_id.backend_id.id

    name = fields.Char(
        string='Name',
        help="The name of the method on the backend",
        required=True
    )
    shop_group_id = fields.Many2one(
        comodel_name='prestashop.shop.group',
        string='PrestaShop Shop Group',
        required=True,
        ondelete='cascade',
    )
    odoo_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='WareHouse',
        required=True,
        readonly=False,
        ondelete='cascade',
    )
    backend_id = fields.Many2one(
        # compute='_compute_backend_id',
        comodel_name='prestashop.backend',
        string='PrestaShop Backend',
        store=True,
    )
    company_id = fields.Many2one(
        related='backend_id.company_id',
        comodel_name="res.company",
        string='Company'
    )

    default_url = fields.Char('Default url')
    #     prestashop_category_ids = fields.One2many('prestashop.product.category','default_shop_id','Categories')


class ShopAdapter(Component):
    _name = 'prestashop.shop'
    _inherit = 'prestashop.adapter'
    _prestashop_model = 'shops'
    _apply_on = 'prestashop.shop'


class ShopBinder(Component):
    _name = 'prestashop.shop.binder'
    _inherit = 'prestashop.binder'
    _apply_on = 'prestashop.shop'
