# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models, fields, api, exceptions, _
from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class PrestashopDeliveryCarrier(models.Model):
    _name = 'prestashop.delivery.carrier'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'delivery.carrier': 'odoo_id'}
    _description = 'PrestaShop Carriers'

    odoo_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Delivery carrier',
        required=True,
        ondelete='cascade',
    )
    id_reference = fields.Integer(
        string='Reference ID',
        help="In PrestaShop, carriers can be copied with the same 'Reference "
             "ID' (only the last copied carrier will be synchronized with the "
             "ERP)"
    )
    name_ext = fields.Char(
        string='Name in PrestaShop',
    )
    active_ext = fields.Boolean(
        string='Active in PrestaShop',
    )
    export_tracking = fields.Boolean(
        string='Export tracking numbers to PrestaShop',
    )
    old_table_id = fields.Integer(string='Old Table ID')

    @api.constrains('backend_id', 'odoo_id', 'id_reference')
    def _check_odoo_id_ref_uniq(self):
        res = {}
        #         record_have_multiple_biding = self.env['ir.config_parameter'].get_param('prestashop.multiple_binding')
        #         if record_have_multiple_biding:
        #             return
        cr = self._cr
        query = 'SELECT "{}", "{}", "{}" FROM "{}" '.format(
            "backend_id",
            "odoo_id",
            "id_reference",
            self._table,
        )
        cr.execute(query)
        for backend_id, odoo_id, id_ref in cr.fetchall():
            if not odoo_id:
                continue
            if (backend_id, odoo_id, id_ref) not in res:
                res[(backend_id, odoo_id, id_ref)] = 1
            else:
                raise exceptions.ValidationError(
                    _(
                        "Multiple bindings for a record in {} with odoo ID {} and "
                        "id_reference {}".format(self._name, odoo_id, id_ref)
                    )
                )


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    carrier_name = fields.Char('PS Carrier Name')
    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.delivery.carrier',
        inverse_name='odoo_id',
        string='PrestaShop Bindings',
    )


class DeliveryCarrierAdapter(Component):
    _name = 'prestashop.delivery.carrier.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.delivery.carrier'
    _prestashop_model = 'carriers'

    def search(self, filters=None):
        if filters is None:
            filters = {}
        filters["filter[deleted]"] = 0
        return super().search(filters)


class DeliveryCarrierBinder(Component):
    _name = 'prestashop.delivery.carrier.binder'
    _inherit = 'prestashop.binder'
    _apply_on = 'prestashop.delivery.carrier'
