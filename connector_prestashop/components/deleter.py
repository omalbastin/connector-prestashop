# © 2016-Today Omal Bastin <omalbastin@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent
from odoo import _


class PrestashopDeleter(AbstractComponent):
    """Base deleter for PrestaShop"""

    _name = "prestashop.deleter"
    _inherit = ["base.deleter", "base.prestashop.connector"]
    _usage = "prestashop.deleter"

    def run(self, external_id, attributes=None):
        """Run the synchronization, delete the record on PrestaShop

        :param external_id: identifier of the record to delete
        """
        resource = self.backend_adapter._prestashop_model
        if 'resource' in attributes:
            resource = attributes.get('resource', resource)
        self.backend_adapter.delete(resource, external_id, attributes)
        return _("Record %s deleted on PrestaShop on resource %s") % (
            external_id,
            resource,
        )
