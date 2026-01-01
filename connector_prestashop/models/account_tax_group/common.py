# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models
from odoo.addons.component.core import Component


class AccountTaxGroup(models.Model):
    _inherit = 'account.tax.group'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.account.tax.group',
        inverse_name='odoo_id',
        string='PrestaShop Bindings',
        readonly=True
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        index=True,
        required=True,
        string='Company',
        default=lambda self: self.env.company
    )
    tax_ids = fields.One2many(
        comodel_name='account.tax',
        inverse_name='tax_group_id',
        string='Taxes',
    )


class PrestashopAccountTaxGroup(models.Model):
    _name = 'prestashop.account.tax.group'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'account.tax.group': 'odoo_id'}
    _description = "Account Tax Group Prestashop Bindings: tax_rule_groups"

    odoo_id = fields.Many2one(
        comodel_name='account.tax.group',
        string='Tax Group',
        required=True,
        ondelete='cascade',
    )


class TaxGroupAdapter(Component):
    _name = 'prestashop.account.tax.group.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.account.tax.group'

    _prestashop_model = 'tax_rule_groups'

    def search(self, filters=None):
        if filters is None:
            filters = {}
        # deleted does not exist in 1.5 version. Not sure when it arrived though
        # adapt the version if needed.
        if self.work.collection.version > "1.5":
            filters["filter[deleted]"] = 0
        return super().search(filters)


class AccountTaxGroupBinder(Component):
    _name = 'prestashop.account.tax.group.binder'
    _inherit = 'prestashop.binder'
    _apply_on = 'prestashop.account.tax.group'
