# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import timedelta

from odoo import models, fields, api
from odoo.addons.component.core import Component
from prestapyt import PrestaShopWebServiceDict

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.sale.order',
        inverse_name='odoo_id',
        string='PrestaShop Bindings',
    )
    # ps_backend_id = fields.Many2one('prestashop.backend', related='prestashop_bind_ids.backend_id', string='Backend')
    ps_order_state_id = fields.Many2one(
        'sale.order.state',
        'PS Order Status',
        tracking=5,
        help="This should be manually changed to update in Prestashop")

    # def _create_delivery_line(self, carrier, price_unit):
    #     sol = super()._create_delivery_line(carrier, price_unit)
    #     from_prestashop = self.env.context.get('from_prestashop', False)
    #     if from_prestashop:
    #         sol.price_unit = price_unit
    #
    #     return sol


class PrestashopSaleOrder(models.Model):
    _name = 'prestashop.sale.order'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'sale.order': 'odoo_id'}
    _description = "prestashop orders"

    odoo_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        required=True,
        ondelete='cascade',
    )
    prestashop_order_line_ids = fields.One2many(
        comodel_name='prestashop.sale.order.line',
        inverse_name='prestashop_order_id',
        string='PrestaShop Order Lines',
    )
    prestashop_discount_line_ids = fields.One2many(
        comodel_name='prestashop.sale.order.line.discount',
        inverse_name='prestashop_order_id',
        string='PrestaShop Discount Lines',
    )
    prestashop_invoice_number = fields.Char('PrestaShop Invoice Number')
    prestashop_delivery_number = fields.Char('PrestaShop Delivery Number')
    total_amount = fields.Float(
        string='Total amount in PrestaShop',
        digits="Account",
        readonly=True,
    )
    total_amount_tax = fields.Float(
        string='Total tax in PrestaShop',
        digits="Account",
        readonly=True,
    )
    total_shipping_tax_included = fields.Float(
        string="Total shipping(inc.) in PrestaShop",
        digits="Account",
        readonly=True,
    )
    total_shipping_tax_excluded = fields.Float(
        string='Total shipping(exc.) in PrestaShop',
        digits="Account",
        readonly=True,
    )
    total_discounts = fields.Float(
        string='Total Discounts in PrestaShop',
        digits="Account",
        readonly=True,
    )
    total_discounts_tax_incl = fields.Float(
        string='Total Discounts(inc.) in PrestaShop',
        digits="Account",
        readonly=True,
    )
    total_discounts_tax_excl = fields.Float(
        string='Total Discounts(exc.) in PrestaShop',
        digits="Account",
        readonly=True,
    )

    def import_orders_since(self, backend, since_date=None, **kwargs):
        """ Prepare the import of orders modified on PrestaShop """
        filters = None
        if since_date:
            filters = {'date': '1', 'filter[date_upd]': '>[%s]' % (since_date)}
        now_fmt = fields.Datetime.now()
        self.env['prestashop.sale.order'].import_batch(
            backend, filters=filters, priority=5, max_retries=0)
        if since_date:
            filters = {'date': '1', 'filter[date_add]': '>[%s]' % since_date}
        self.env['prestashop.mail.message'].with_delay(
            priority=10, eta=60 * 5,
            description=f"Batch import prestashop.mail.message with filters {filters}",
        ).import_batch(backend, filters)
        self.env['prestashop.mail.message.other'].with_delay(
            priority=10, eta=60 * 5,
            description=f"Batch import prestashop.mail.message.other with filters {filters}",
        ).import_batch(backend, filters)

        # substract a 10 second margin to avoid to miss an order if it is
        # created in prestashop at the exact same time odoo is checking.
        next_check_datetime = now_fmt - timedelta(seconds=10)
        backend.import_orders_since = next_check_datetime
        return True

    def export_tracking_number(self):
        """ Export the tracking number of a delivery order. """
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='tracking.exporter')
            return exporter.run(self)

    #     def find_prestashop_state(self):
    #         self.ensure_one()
    #         state_list_model = self.env['sale.order.state.list']
    #         state_lists = state_list_model.search(
    #             [('name', '=', self.state)]
    #         )
    #         for state_list in state_lists:
    #             if state_list.prestashop_state_id.backend_id == self.backend_id:
    #                 return state_list.prestashop_state_id.prestashop_id
    #
    #         return None

    def export_sale_state(self):
        for sale_binding in self:
            with sale_binding.backend_id.work_on(self._name) as work:
                exporter = work.component(usage="sale.order.state.exporter")
                binder = exporter.binder_for("prestashop.sale.order.state")
                new_stateps_id = binder.to_external(
                    sale_binding.ps_order_state_id, wrap=True
                )
                return exporter.run(sale_binding, new_stateps_id)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.sale.order.line',
        inverse_name='odoo_id',
        string='PrestaShop Bindings',
    )
    prestashop_discount_bind_ids = fields.One2many(
        comodel_name='prestashop.sale.order.line.discount',
        inverse_name='odoo_id',
        string='PrestaShop Discount Bindings',
    )


class PrestashopSaleOrderLine(models.Model):
    _name = 'prestashop.sale.order.line'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'sale.order.line': 'odoo_id'}
    _description = "prestashop order_details"

    odoo_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sale Order line',
        required=True,
        ondelete='cascade',
    )
    prestashop_order_id = fields.Many2one(
        comodel_name='prestashop.sale.order',
        string='PrestaShop Sale Order',
        required=True,
        ondelete='cascade',
        index=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            ps_sale_order = self.env['prestashop.sale.order'].search([
                ('id', '=', vals['prestashop_order_id'])
            ], limit=1)
            vals['order_id'] = ps_sale_order.odoo_id.id
        return super().create(vals_list)


class PrestashopSaleOrderLineDiscount(models.Model):
    _name = 'prestashop.sale.order.line.discount'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'sale.order.line': 'odoo_id'}
    _description = "prestashop order_discounts"

    odoo_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Sale Order line',
        required=True,
        ondelete='cascade',
    )
    prestashop_order_id = fields.Many2one(
        comodel_name='prestashop.sale.order',
        string='PrestaShop Sale Order',
        required=True,
        ondelete='cascade',
        index=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            ps_sale_order = self.env['prestashop.sale.order'].search([
                ('id', '=', vals['prestashop_order_id'])
            ], limit=1)
            vals['order_id'] = ps_sale_order.odoo_id.id
        return super().create(vals_list)


class OrderPaymentModel(models.TransientModel):
    # In actual connector version is mandatory use a model
    _name = '__not_exist_prestashop.payment'
    _description = "Dummy Transient model for Order Payment"


class SaleOrderAdapter(Component):
    _name = 'prestashop.sale.order.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.sale.order'

    _prestashop_model = 'orders'
    _export_node_name = 'order'

    def update_sale_state(self, prestashop_id, datas):
        return self.client.add('order_histories', datas)

    def search(self, filters=None):
        result = super().search(filters=filters)
        shops = self.env["prestashop.shop"].search(
            [("backend_id", "=", self.backend_record.id)]
        )
        for shop in shops:
            if not shop.default_url:
                continue
            api = PrestaShopWebServiceDict(
                "%s/api" % shop.default_url, self.prestashop.webservice_key
            )
            result += api.search(self._prestashop_model, filters)
        return result


class SaleOrderBinder(Component):
    _name = 'prestashop.sale.order.binder'
    _inherit = 'prestashop.binder'
    _apply_on = 'prestashop.sale.order'


class SaleOrderLineAdapter(Component):
    _name = 'prestashop.sale.order.line.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.sale.order.line'
    _prestashop_model = 'order_details'


class SaleOrderLineBinder(Component):
    _name = 'prestashop.sale.order.line.binder'
    _inherit = 'prestashop.binder'
    _apply_on = 'prestashop.sale.order.line'


class OrderDiscountAdapter(Component):
    _name = 'prestashop.sale.order.line.discount.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.sale.order.line.discount'

    #     _prestashop_model = 'order_discounts'

    @property
    def _prestashop_model(self):
        return self.backend_record.get_version_ps_key('order_discounts')


class OrderPaymentAdapter(Component):
    _name = '__not_exist_prestashop.payment.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = '__not_exist_prestashop.payment'
    _prestashop_model = 'order_payments'
