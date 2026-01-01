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


class PrestashopProductTemplate(models.Model):
    _inherit = "prestashop.product.template"

    def copy_data(self, default=None):
        vals_list = super().copy_data(default)
        for product, vals in zip(self, vals_list):
            vals['image_ids'] = []
        return vals_list
#
#
# class ProductTemplate(models.Model):
#     _inherit = "product.template"
#


    # def button_delete_extra_image_from_ps(self):
    #     self.job_delete_extra_images_from_ps(self)
    #     return True

    # def job_delete_extra_images_from_ps(self, products):
    #     for each in products:
    #         each.with_delay().job_delete_extra_images_from_each_ps_product()


