# © 2016-TODAY Omal Bastin(O4 ODOO) <omalbastin@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo.addons.component.core import AbstractComponent, Component
from odoo.addons.component_event import skip_if

_logger = logging.getLogger(__name__)

class ProductTemplateListener(Component):
    _inherit = 'product.template.listener'

    def _ps_needed_fields(self):
        res = super()._ps_needed_fields()
        res.update("image_ids")
        return res

class PrestashopProductTemplateListener(Component):
    _inherit = 'prestashop.product.template.listener'

    def _ps_needed_fields(self):
        res = super()._ps_needed_fields()
        res.update("image_ids")
        return res
