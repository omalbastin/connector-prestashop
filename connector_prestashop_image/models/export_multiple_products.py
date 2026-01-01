# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import functools

from odoo import models, fields


class ExportMultipleProducts(models.TransientModel):
    _inherit = 'export.multiple.products'

    def _check_images(self, product):
        for variant in product.product_variant_ids:
            for image in variant.image_ids:
                if image.owner_id != product.id:
                    image.product_id = product

    def check_missing(self, product):
        super().check_missing(product)
        self._check_images(product)
