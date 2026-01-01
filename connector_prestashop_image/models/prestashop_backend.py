# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

import pytz
from odoo.addons.component.core import Component

from odoo import fields, models

try:
    import slugify as slugify_lib
except ImportError:
    slugify_lib = None

_logger = logging.getLogger(__name__)


class PrestashopBackend(models.Model):
    _inherit = "prestashop.backend"

    import_export_images = fields.Selection(
        [
            ("none", "Import/Export Not Activated"),
            ("import", "Import Only"),
            ("export", "Export Only"),
            ("import_export", "Import and Export"),
        ],
        "Product Images",
        default="none",
    )

    def export_all_images(self):
        for binding in self.env["prestashop.product.image"].search(
                [
                    ("backend_id", "=", self.id),
                    # ('prestashop_id', 'in', prestashop_ids),
                    ("prestashop_id", "!=", 0),
                    # ('ps_active', '=', True),
                    # ("updated_new_field", "=", True),
                ]
        ):
            # binding.write({'ps_active_date': six_months_old})
            binding.with_context(connector_delay=True).re_export()
        return True

    def button_export_categ_images(self):
        """ Export categ on PrestaShop """
        for backend_record in self:
            for binding in self.env['prestashop.product.category'].search(
                    [('backend_id', '=', backend_record.id)]):
                for image_binding in binding.image_ids.mapped('prestashop_bind_ids'):
                    image_binding.with_context(connector_delay=True).re_export()
        return True


