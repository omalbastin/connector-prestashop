# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models
from odoo.addons.component.core import Component


class OrderCarrierModel(models.TransientModel):
    # In actual connector version is mandatory use a model
    _name = '__not_exit_prestashop.order_carrier'
    _description = "Dummy Transient model for Order Carrier"


class OrderCarriers(Component):
    _name = 'prestashop.order_carrier.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = '__not_exit_prestashop.order_carrier'

    _prestashop_model = 'order_carriers'
    _export_node_name = 'order_carrier'
    _export_node_name_res = 'order_carrier'
