# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class SyncProducts(models.TransientModel):
    _name = 'sync.products'
    _description = "Sync product transient model"

    def _bind_resync(self, product_ids):
        products = self.env['product.template'].browse(product_ids)
        for product in products:
            try:
                for bind in product.prestashop_bind_ids:
                    bind.resync()
            except Exception as e:
                _logger.debug('id %s, attributes %s\n', str(product.id), e)

    def re_export_products(self):
        products = self.env['product.template'].browse(self.env.context['active_ids'])
        for product in products:
            try:
                for bind in product.prestashop_bind_ids:
                    bind.with_context(connector_delay=True).re_export()
            except Exception as e:
                _logger.debug('id %s, attributes %s\n', str(product.id), e)

    def sync_products(self):
        self._bind_resync(self.env.context['active_ids'])

    def sync_all_products(self):
        self._bind_resync([])
