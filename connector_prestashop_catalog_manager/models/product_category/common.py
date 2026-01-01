# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class ProductCategory(models.Model):
    _inherit = 'product.category'

    active_ext = fields.Boolean('Active in PS', default=True)


class PrestashopProductCategory(models.Model):
    _inherit = 'prestashop.product.category'

    active_ext = fields.Boolean(related='odoo_id.active_ext')

    @api.onchange('link_rewrite')
    def onchange_link_rewrite(self):
        if self.link_rewrite:
            self.link_rewrite = self.backend_id.get_slug(self.link_rewrite)
