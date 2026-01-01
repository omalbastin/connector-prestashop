# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class SyncProducts(models.TransientModel):
    _name = 'active.deactive.products'
    _description = "active or deactivate products in ps"

    force_status = fields.Boolean(
        string='Force Status',
        help='Check this option to force active product in prestashop')

    def update_bindings(self, product, status):
        for bind in product.with_context(active_test=False).prestashop_bind_ids:
            if bind.ps_active != status or self.force_status:
                bind.ps_active = status
                bind.available_for_order = status
            # product.ps_active = status
            # product.ps_active_date = False
                if status:
                    product.ps_active_date = fields.Datetime.now()

    def _change_status(self, status):
        self.ensure_one()
        product_obj = self.env['product.template']
        for product in product_obj.browse(self.env.context['active_ids']):
            self.update_bindings(product, status)

    def active_products(self):
        self._change_status(True)

    def deactive_products(self):
        self._change_status(False)


class SyncCategories(models.TransientModel):
    _name = 'active.deactive.category'
    _description = "activate or deactivate categories in ps"

    force_status = fields.Boolean(
        string='Force Status',
        help='Check this option to force active category in prestashop')

    def _change_status(self, status):
        self.ensure_one()
        category_obj = self.env['product.category']
        for category in category_obj.browse(self.env.context['active_ids']):
            for bind in category.prestashop_bind_ids:
                if bind.active_ext != status or self.force_status:
                    bind.active_ext = status
                    category.active_ext = status
                    bind.with_context(connector_delay=True).re_export()

    def active_products(self):
        self._change_status(True)

    def deactive_products(self):
        self._change_status(False)
