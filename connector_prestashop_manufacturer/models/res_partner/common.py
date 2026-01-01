# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import models, fields, api
from odoo.addons.component.core import Component


class ResPartner(models.Model):
    _inherit = "res.partner"

    prestashop_manufacturer_bind_ids = fields.One2many(
        comodel_name='prestashop.manufacturer',
        inverse_name='odoo_id',
        string='PrestaShop Manufacturer Binding',
    )

    prestashop_manufacturer_address_bind_ids = fields.One2many(
        comodel_name='prestashop.manufacturer.address',
        inverse_name='odoo_id',
        string='PrestaShop Manufacturer Address Binding',
    )


class PrestashopManufacturer(models.Model):
    _name = 'prestashop.manufacturer'
    _description = 'PrestaShop Manufacturers'
    _inherit = [
        'prestashop.binding.odoo',
        'prestashop.partner.mixin',
    ]
    _inherits = {'res.partner': 'odoo_id'}

    backend_id = fields.Many2one(
        comodel_name='prestashop.backend',
        string='PrestaShop Backend',
        readonly=True,
    )
    odoo_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
        ondelete='cascade',
    )
    id_reference = fields.Integer(
        string='Reference ID',
        help="In PrestaShop, carriers can be copied with the same 'Reference "
             "ID' (only the last copied carrier will be synchronized with the "
             "ERP)"
    )
    link_rewrite = fields.Char(string='Friendly URL', translate=False)
    name_ext = fields.Char(
        string='Name in PrestaShop',
    )
    active_ext = fields.Boolean(
        string='Active in PrestaShop', default=True
    )
    group_ids = fields.Many2many(
        comodel_name='prestashop.res.partner.category',
        relation='prestashop_category_manufacturer',
        column1='partner_id',
        column2='category_id',
        string='PrestaShop Groups',
    )

    @api.onchange('name', 'link_rewrite')
    def onchange_link_rewrite(self):
        get_slug = self.env['prestashop.backend'].get_slug
        if self.name and not self.link_rewrite:
            self.link_rewrite = get_slug(self.link_rewrite)
        if self.link_rewrite:
            self.link_rewrite = get_slug(self.link_rewrite)

    def import_manufacturers(self, backend, since_date, **kwargs):
        filters = None
        if since_date:
            filters = {'date': '1',
                       'filter[date_upd]': '>[%s]' % since_date}
        now_fmt = fields.Datetime.now()

        result = self.import_batch_merge(backend, filters, **kwargs)
        backend.import_manufacturers_since = now_fmt
        return result


#     @api.model
#     def export_manufacturer(self, partner_record_id, fields=None, **kwargs):
#         """ Export supplier partner as manufacturer. """
#     
#         binding_model = 'prestashop.manufacturer'
#         env = self.get_environment(binding_model)
#         exporter = env.get_connector_unit(ManufacturerExporter)
#         binding = exporter._get_or_create_binding(
#             self.env['res.partner'].browse(partner_record_id),
#             binding_model
#         )
#         return exporter.run(binding.id, fields, **kwargs)


class PrestashopManufacturerAddress(models.Model):
    _name = 'prestashop.manufacturer.address'
    _inherit = [
        'prestashop.binding.odoo',
        'prestashop.address.mixin',
    ]
    _inherits = {'res.partner': 'odoo_id'}
    _rec_name = 'odoo_id'

    odoo_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
        ondelete='cascade',
    )
    prestashop_partner_id = fields.Many2one(
        comodel_name='prestashop.manufacturer',
        string='PrestaShop Manufacturer',
        required=True,
        ondelete='cascade',
    )
    backend_id = fields.Many2one(
        comodel_name='prestashop.backend',
        string='PrestaShop Backend',
        related='prestashop_partner_id.backend_id',
        store=True,
        readonly=True,
    )


class ManufacturerAdapter(Component):
    _name = 'prestashop.manufacturer.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.manufacturer'

    _prestashop_model = 'manufacturers'
    _export_node_name = 'manufacturer'
    _export_node_name_res = 'manufacturer'


#     def search(self, filters=None):
#         if filters is None:
#             filters = {}
#         return super(ManufacturerAdapter, self).search(filters)


class ManufacturerBinder(Component):
    _name = 'prestashop.manufacturer.binder'
    _inherit = 'prestashop.binder'
    _apply_on = 'prestashop.manufacturer'


class ManufacturerAddressAdapter(Component):
    _name = 'prestashop.manufacturer.address.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.manufacturer.address'

    _prestashop_model = 'addresses'
    _export_node_name = 'address'
    _export_node_name_res = 'address'


class ManufacturerAddressBinder(Component):
    _name = 'prestashop.manufacturer.address.binder'
    _inherit = 'prestashop.binder'
    _apply_on = 'prestashop.manufacturer.address'
