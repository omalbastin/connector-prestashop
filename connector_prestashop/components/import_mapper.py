# © 2016-Today Omal Bastin <omalbastin@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent
from odoo.addons.connector.components.mapper import mapping


class PrestashopImportMapper(AbstractComponent):
    _name = 'prestashop.import.mapper'
    _inherit = ['base.prestashop.connector', 'base.import.mapper']
    _usage = 'prestashop.import.mapper'

    _map_child_usage = "prestashop.import.map.child"

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


# Mainly for managing the sale order line
class ImportMapChild(AbstractComponent):
    """ :py:class:`MapChild` for the Imports """
    _name = "prestashop.map.child.import"
    _inherit = 'base.map.child.import'
    _usage = "prestashop.import.map.child"

    def _child_mapper(self):
        return self.component(usage='prestashop.import.mapper')

    def format_items(self, items_values):
        """ Format the values of the items mapped from the child Mappers.

        It can be overridden for instance to add the Odoo
        relationships commands ``(6, 0, [IDs])``, ...

        As instance, it can be modified to handle update of existing
        items: check if an 'id' has been defined by
        :py:meth:`get_item_values` then use the ``(1, ID, {values}``)
        command

        :param items_values: list of values for the items to create
        :type items_values: list

        """
        result = []
        for values in items_values:
            if values.get('id'):
                rec_id = values.pop('id')
                result.append((1, rec_id, values))
            else:
                result.append((0, 0, values))
        return result
