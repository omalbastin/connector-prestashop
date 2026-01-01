# © 2016-TODAY Omal Bastin(Steigend IT Solutions) <omalbastin@steigendit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping

from odoo import models

_logger = logging.getLogger(__name__)
try:
    from prestapyt import PrestaShopWebServiceError
except ImportError:
    _logger.debug("Cannot import from `prestapyt`")


class ProductTemplateImporter(Component):
    _inherit = "prestashop.product.template.importer"

    def _delay_product_image_variant(self, combinations, **kwargs):
        delayable = self.env["prestashop.product.product"].with_delay(priority=15)
        delayable.set_product_image_variant(self.backend_record, combinations, **kwargs)

    def import_combinations(self):
        super().import_combinations()
        prestashop_record = self._get_prestashop_data()
        associations = prestashop_record.get("associations", {})

        ps_key = self.backend_record.get_version_ps_key("combinations")
        combinations = associations.get("combinations", {}).get(ps_key, [])
        if not isinstance(combinations, list):
            combinations = [combinations]
        first_exec = False
        if combinations:
            first_exec = combinations.pop(
                combinations.index(
                    {"id": prestashop_record["id_default_combination"]["value"]}
                )
            )
        if self.backend_record.import_export_images in ["import", "import_export"]:
            if combinations and associations["images"].get("image"):
                self._delay_product_image_variant([first_exec] + combinations)

    def _after_import(self, binding):
        res = super()._after_import(binding)
        if self.backend_record.import_export_images in ["import", "import_export"]:
            self.import_images(binding)

    def import_images(self, binding):
        prestashop_record = self._get_prestashop_data()
        associations = prestashop_record.get("associations", {})
        images = associations.get("images", {}).get(
            self.backend_record.get_version_ps_key("image"), {}
        )
        if not isinstance(images, list):
            images = [images]
        for image in images:
            if image.get("id"):
                delayable = self.env["prestashop.product.image"].with_delay(priority=10)
                delayable.import_product_image(
                    self.backend_record, prestashop_record["id"], image["id"]
                )
