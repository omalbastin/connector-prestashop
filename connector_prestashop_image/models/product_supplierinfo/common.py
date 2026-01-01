# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component

from odoo import models
from odoo.addons.connector_prestashop.components.backend_adapter import PrestaShopWebServiceImage


class SupplierImageModel(models.TransientModel):
    # In actual connector version is mandatory use a model
    _name = "prestashop.supplier.image"
    _description = "Dummy Supplier Image Transient model"


class SupplierImageAdapter(Component):
    _name = "prestashop.supplier.image.adapter"
    _inherit = "prestashop.adapter"
    _apply_on = "prestashop.supplier.image"
    # pylint: disable=method-required-super

    _prestashop_image_model = "suppliers"

    def read(self, supplier_id, options=None):
        client = PrestaShopWebServiceImage(
            self.prestashop.api_url, self.prestashop.webservice_key
        )
        res = client.get_image(
            self._prestashop_image_model, supplier_id, options=options
        )
        return res["content"]
