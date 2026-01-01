# © 2016-TODAY Omal Bastin(Steigend IT Solutions) <omalbastin@steigendit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component

from odoo import fields, models  # , api, exceptions, _


class PrestashopResCountryState(models.Model):
    _name = "prestashop.res.country.state"
    _inherit = "prestashop.binding"
    _inherits = {"res.country.state": "odoo_id"}
    _description = "prestashop states"

    odoo_id = fields.Many2one(
        comodel_name="res.country.state",
        required=True,
        ondelete="cascade",
        string="Federal States",
    )


class ResCountryState(models.Model):
    _inherit = "res.country.state"

    prestashop_bind_ids = fields.One2many(
        comodel_name="prestashop.res.country.state",
        inverse_name="odoo_id",
        copy=False,
        related="",
        store=True,
        inherited=False,
        inherited_field=None,
        string="prestashop Bindings",
    )


class ResCountryStateAdapter(Component):
    _name = "prestashop.res.country.state.adapter"
    _inherit = "prestashop.adapter"
    _apply_on = "prestashop.res.country.state"
    _prestashop_model = "states"


class ResCountryStateBinder(Component):
    _name = "prestashop.res.country.state.binder"
    _inherit = "prestashop.binder"
    _apply_on = "prestashop.res.country.state"
