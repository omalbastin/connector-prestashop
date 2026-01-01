# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models, fields
from odoo.addons.component.core import Component


class SaleOrderState(models.Model):
    _name = "sale.order.state"
    _description = "Sale Order States"

    name = fields.Char('Name', translate=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    default_shop_id = fields.Many2one(comodel_name='prestashop.shop')
    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.sale.order.state',
        inverse_name='odoo_id',
        string='PrestaShop Bindings',
    )


class PrestashopSaleOrderState(models.Model):
    _name = 'prestashop.sale.order.state'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'sale.order.state': 'odoo_id'}
    _description = "Sale order state prestashop bindings: order_states"

    #     openerp_state_ids = fields.One2many(
    #         comodel_name='sale.order.state.list',
    #         inverse_name='prestashop_state_id',
    #         string='Odoo States',
    #     )
    odoo_id = fields.Many2one(
        comodel_name='sale.order.state',
        required=True,
        ondelete='cascade',
        string='Sale Order State',
    )


# #not using the lists
# class SaleOrderStateList(models.Model):
#     _name = 'sale.order.state.list'
# 
#     name = fields.Selection(
#         selection=[
#             ('draft', 'Draft Quotation'),
#             ('sent', 'Quotation Sent'),
#             ('cancel', 'Cancelled'),
#             ('waiting_date', 'Waiting Schedule'),
#             ('progress', 'Sales Order'),
#             ('manual', 'Sale to Invoice'),
#             ('invoice_except', 'Invoice Exception'),
#             ('done', 'Done')
#         ],
#         string='Odoo State',
#         required=True,
#     )
# #  #odoo10   [
# #         ('draft', 'Quotation'),
# #         ('sent', 'Quotation Sent'),
# #         ('sale', 'Sales Order'),
# #         ('done', 'Locked'),
# #         ('cancel', 'Canceled')]
#     prestashop_state_id = fields.Many2one(
#         comodel_name='prestashop.sale.order.state',
#         string='PrestaShop State',
#     )
#     prestashop_id = fields.Integer(
#         related='prestashop_state_id.prestashop_id',
#         readonly=True,
#         store=True,
#         string='PrestaShop ID',
#     )


class SaleOrderStateAdapter(Component):
    _name = 'prestashop.sale.order.state.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.sale.order.state'
    _prestashop_model = 'order_states'
