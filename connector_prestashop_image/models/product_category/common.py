# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component

from odoo import models
from odoo.addons.connector_prestashop_image.components.backend_adapter import PrestaShopWebServiceImage

#TODO in future remove dependency to base_multi_image module for categories as category doesnot need multiple images

# class CategoryImageModel(models.TransientModel):
#     # In actual connector version is mandatory use a model
#     _name = "prestashop.category.image"
#     _description = "Dummy Category Image Transient model"
#
#
# class CategoryImageAdapter(Component):
#     _name = "prestashop.category.image.adapter"
#     _inherit = "prestashop.adapter"
#     _apply_on = "prestashop.category.image"
#     # pylint: disable=method-required-super
#
#     _prestashop_image_model = "categories"
#
#     def read(self, category_id, options=None):
#         client = PrestaShopWebServiceImage(
#             self.prestashop.api_url, self.prestashop.webservice_key
#         )
#         res = client.get_image(
#             self._prestashop_image_model, category_id, options=options
#         )
#         return res["content"]
