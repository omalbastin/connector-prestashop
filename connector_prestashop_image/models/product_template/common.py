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

    # def job_delete_extra_images_from_each_ps_product(self):
    #     ms_backend = self.env['prestashop.backend'].browse(4)
    #     with ms_backend.work_on('prestashop.product.image') as work:
    #         image_adapter = work.component(usage='backend.adapter')
    #         product_adapter = work.component(usage='backend.adapter', model_name='prestashop.product.template')
    #         psapi = image_adapter.client
    #         for binding in self.mapped('prestashop_bind_ids').filtered(
    #                 lambda x: x.backend_id.id == 4 and x.prestashop_id):
    #             filters = {'filter[id]': binding.prestashop_id}
    #             prestashop_record_id = product_adapter.search(filters)
    #             if not prestashop_record_id:
    #                 #                 logmessage = (_("Prestashop id %s not found for minischoggi"%(binding.prestashop_id)))
    #                 #                 binding.odoo_id.message_post(body=logmessage)
    #                 continue
    #             #             ps_image_ids = []
    #             #             for image in binding.odoo_id.image_ids:
    #             #                 ps_image_id = image_binder.to_external(image, wrap=True)
    #             #                 ps_image_ids.append(ps_image_id)
    #             resource = '/images/products/%s' % binding.prestashop_id
    #             res = psapi.search(resource, options=None)
    #             for ext_ps_id in res:
    #                 #                 if ext_ps_id not in ps_image_ids:
    #                 rem_resource = "%s/%s" % (resource, ext_ps_id)
    #                 self.env['prestashop.product.image'].with_delay().export_delete_record(ms_backend, ext_ps_id,
    #                                                                                        dict(resouce=rem_resource))
    #             binding.odoo_id.image_ids.mapped('prestashop_bind_ids').write({'prestashop_id': 0})

