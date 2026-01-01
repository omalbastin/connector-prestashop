# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from odoo.addons.component.core import Component


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # in multiple ps integrations, Sometimes refernce will be the matching key and in some case upc will be the
    # matching key. So based on the configuration in backend, we save the value here in ps_default_code
    # for matching.
    ps_default_code = fields.Char('Prestashop Default Code', help="Matching Reference/UPC")
    # prestashop_bind_ids = fields.One2many(
    #     comodel_name='prestashop.product.combination',
    #     inverse_name='odoo_id',
    #     copy=False,
    #     string='PrestaShop Bindings',
    # )
    prestashop_combinations_bind_ids = fields.One2many(
        comodel_name='prestashop.product.product',
        inverse_name='odoo_id',
        string='PrestaShop Bindings (combinations)',
    )
    default_on = fields.Boolean("Default PS Combination?")
    impact_price = fields.Float(string="Price Impact", digits="Product Price")

    def update_prestashop_qty(self):
        for product in self:
            product_template = product.product_tmpl_id
            has_combinations = len(product_template.attribute_line_ids) > 0
            if has_combinations:
                # Recompute qty in combination binding
                for combination_binding in product.prestashop_combinations_bind_ids:
                    combination_binding.recompute_prestashop_qty()
            # Recompute qty in product template binding if any combination
            # if modified
            for prestashop_product in product.product_tmpl_id.prestashop_bind_ids:
                prestashop_product.recompute_prestashop_qty()

    def update_prestashop_quantities(self):
        """Update prestashop combination quantity"""
        for product in self:
            product_template = product.product_tmpl_id
            prestashop_combinations = (
                                              len(product_template.attribute_line_ids) > 0
                                              and product_template.product_variant_ids
                                      ) or []
            if not prestashop_combinations:
                for prestashop_product in product_template.prestashop_bind_ids:
                    prestashop_product.sudo().recompute_prestashop_qty()
            else:
                for prestashop_combination in prestashop_combinations:
                    for combination_binding in \
                            prestashop_combination.prestashop_combinations_bind_ids:
                        combination_binding.sudo().recompute_prestashop_qty()
        return True

    @api.depends("impact_price")
    def _compute_product_price_extra(self):
        for product in self:
            if product.impact_price:
                product.price_extra = product.impact_price
            else:
                product.price_extra = sum(
                    product.mapped("product_template_attribute_value_ids.price_extra")
                )

    def _set_variants_default_on(self, default_on_list=None):
        if self.env.context.get('skip_check_default_variant', False):
            return True
        templates = self.mapped('product_tmpl_id')
        for template in templates:
            variants = template.with_context(
                skip_check_default_variant=True
            ).product_variant_ids.filtered('default_on')
            if not variants:
                active_variants = template.with_context(
                    skip_check_default_variant=True
                ).product_variant_ids.filtered('active')
                active_variants[:1].write({'default_on': True})
            elif len(variants) > 1:
                if default_on_list:
                    variants.filtered(
                        lambda x: x.id not in default_on_list
                    ).write({'default_on': False})
                else:
                    variants[1:].write({'default_on': False})

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res._set_variants_default_on()
        return res

    def write(self, vals):
        if not vals.get('active', True):
            vals['default_on'] = False
        res = super().write(vals)
        default_on_list = vals.get('default_on', False) and self.ids or []
        self._set_variants_default_on(default_on_list)
        return res

    def copy_data(self, default=None):
        vals_list = super().copy_data(default)
        for product, vals in zip(self, vals_list):
            if not product.prestashop_combinations_bind_ids:
                vals['prestashop_combinations_bind_ids'] = []
        return vals_list


    #     def unlink(self):
    #         self.write({
    #             'default_on': False,
    #             'active': False
    #         })
    #         res = super(ProductProduct, self).unlink()
    #         return res

    def open_product_template(self):
        """
        Utility method used to add an "Open Product Template"
        button in product.product views
        """
        self.ensure_one()
        return {'type': 'ir.actions.act_window',
                'res_model': 'product.template',
                'view_mode': 'form',
                'res_id': self.product_tmpl_id.id,
                'target': 'new',
                'flags': {'form': {'action_buttons': True}}}


class PrestashopProductCombination(models.Model):
    _name = 'prestashop.product.product'
    _inherit = [
        "prestashop.binding.odoo",
        "prestashop.product.qty.mixin",
    ]
    _inherits = {'product.product': 'odoo_id'}
    _description = "prestashop combinations"

    odoo_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        ondelete='cascade',
    )
    main_template_id = fields.Many2one(
        comodel_name='prestashop.product.template',
        string='Main Template',
        required=False,
        ondelete='cascade',
    )
    quantity = fields.Float(
        string='Computed Quantity', copy=False,
        help='Last computed quantity to send on PrestaShop.'
    )
    reference = fields.Char(string='Original reference')
    upc = fields.Char('UPC')

    def export_inventory(self, fields=None):
        """ Export the inventory configuration and quantity of a product. """
        backend = self.backend_id
        with backend.work_on('prestashop.product.product') as work:
            exporter = work.component(usage='inventory.exporter')
            return exporter.run(self, fields)

    @api.model
    def export_product_quantities(self, backend=None, manual_update=False):
        if not manual_update:
            self.search([('backend_id', '=', backend.id)]
                        ).recompute_prestashop_qty()
        else:
            self.search([('backend_id', '=', backend.id)]
                        ).manually_recompute_prestashop_qty()

    def set_product_image_variant(self, backend, combination_ids, **kwargs):
        with backend.work_on(self._name) as work:
            importer = work.component(usage="prestashop.importer")
            return importer.set_variant_images(combination_ids, **kwargs)


class ProductAdapter(Component):
    _name = 'prestashop.product.product.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.product.product'
    _prestashop_model = 'combinations'
    _export_node_name = _export_node_name_res = 'combination'


class ProductProductBinder(Component):
    _name = 'prestashop.product.product.binder'
    _inherit = 'prestashop.binder'
    _apply_on = 'prestashop.product.product'
