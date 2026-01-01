# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import functools

from odoo import models, fields


class ExportMultipleProducts(models.TransientModel):
    _name = 'export.multiple.products'

    def _default_backend(self):
        return self.env['prestashop.backend'].search([], limit=1).id

    def _default_shop(self):
        return self.env['prestashop.shop'].search([], limit=1).id

    backend_id = fields.Many2one(
        comodel_name='prestashop.backend',
        default=_default_backend,
        string='Backend',
    )
    shop_id = fields.Many2one(
        comodel_name='prestashop.shop',
        default=_default_shop,
        string='Default Shop',
    )

    def _parent_length(self, categ):
        if not categ.parent_id:
            return 1
        else:
            return 1 + self._parent_length(categ.parent_id)

    def _check_category(self, product):
        if not (product.prestashop_categ_ids):
            return False
        return True

    def _check_variants(self, product):
        if len(product.product_variant_ids) == 1:
            return True
        if (len(product.product_variant_ids) > 1 and
                not product.attribute_line_ids):
            check_count = functools.reduce(
                lambda x, y: x * y, map(lambda x: len(x.value_ids),
                                        product.attribute_line_ids))
            if check_count < len(product.product_variant_ids):
                return False
        return True

    def check_missing(self, product):
        # for future updates
        return True

    def export_variant_stock(self):
        template_obj = self.env['product.template']
        products = template_obj.browse(self.env.context['active_ids'])
        products.update_prestashop_quantities()

    def create_prestashop_template(self, product):
        presta_tmpl_obj = self.env['prestashop.product.template']
        return presta_tmpl_obj.create({
            'backend_id': self.backend_id.id,
            'default_shop_id': self.shop_id.id,
            'link_rewrite': self.backend_id.get_slug(product.name),
            'odoo_id': product.id,
        })

    def export_products(self):
        self.ensure_one()
        product_obj = self.env['product.template']
        presta_tmpl_obj = self.env['prestashop.product.template']
        for product in product_obj.browse(self.env.context['active_ids']):
            presta_tmpl = presta_tmpl_obj.search([
                ('odoo_id', '=', product.id),
                ('backend_id', '=', self.backend_id.id),
                ('default_shop_id', '=', self.shop_id.id),
            ])
            if not presta_tmpl:
                cat = self._check_category(presta_tmpl)
                var = self._check_variants(product)
                self.check_missing(product)
                if not (var and cat):
                    continue
                self.create_prestashop_template(product)
            else:
                for tmpl in presta_tmpl:
                    if ' ' in tmpl.link_rewrite:
                        tmpl.link_rewrite = self.backend_id.get_slug(tmpl.link_rewrite)
