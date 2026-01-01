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


class ProductCombinationImporter(Component):
    _inherit = "prestashop.product.product.importer"

    def set_variant_images(self, combinations):
        backend_adapter = self.component(
            usage="backend.adapter", model_name="prestashop.product.product"
        )
        for combination in combinations:
            record = backend_adapter.read(combination["id"])
            associations = record.get("associations", {})
            try:
                ps_images = associations.get("images", {}).get(
                    self.backend_record.get_version_ps_key("image"), {}
                )
            except PrestaShopWebServiceError:
                # TODO: don't we track anything here? Maybe a checkpoint?
                continue
            binder = self.binder_for("prestashop.product.image")
            if not isinstance(ps_images, list):
                ps_images = [ps_images]
            if "id" in ps_images[0]:
                images = [
                    binder.to_internal(x.get("id"), unwrap=True) for x in ps_images
                ]
            else:
                continue
            product_binder = self.binder_for("prestashop.product.product")
            product = product_binder.to_internal(combination["id"], unwrap=True)
            product.with_context(connector_no_export=True).write(
                {"image_ids": [(6, 0, [x.id for x in images])]}
            )

