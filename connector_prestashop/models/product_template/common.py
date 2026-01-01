# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from collections import defaultdict

import logging

from odoo import api, fields, models, exceptions, _
from odoo.addons.component.core import Component
from ...components.backend_adapter import retryable_error
from prestapyt import PrestaShopWebServiceDict


_logger = logging.getLogger(__name__)


# try:
#     from odoo.addons.connector_prestashop.prestapyt import PrestaShopWebServiceDict
# except ImportError:
#     _logger.debug('Cannot import from `prestapyt`')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    ps_default_code = fields.Char('Prestashop Default Code',
                                  help="Matching Reference/UPC")
    ps_type = fields.Selection(
        [('virtual', 'Virtual'), ('simple', 'Standard'), ('pack', 'Pack')],
        'Prestashop Product Type', default='simple')

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.template',
        inverse_name='odoo_id',
        copy=True,
        string='Prestashop Bindings',
    )

    @api.onchange('categ_id')
    def onchange_categ_id(self):
        if not self.categ_id:
            return
        categ_ids = self._get_full_categ_list(self.categ_id)
        if not self.categ_ids:
            self.categ_ids = [(6, 0, categ_ids.ids)]
        else:
            categ_ids = self.categ_ids.ids + list(categ_ids.ids)
            self.categ_ids = [(6, 0, list(set(categ_ids)))]

    def _get_full_categ_list(self, categ_id):
        """ Return the full parent categ list. """
        #         if level <= 0:
        #             return '...'
        if categ_id.parent_id:
            return self._get_full_categ_list(categ_id.parent_id) + categ_id
        else:
            return categ_id


    def copy_data(self, default=None):
        vals_list = super().copy_data(default)
        for product, vals in zip(self, vals_list):
            default_code = "%s_copy" % self.default_code  # self.get_next_code('default_code', self.default_code)
            ps_default_code = "%s_copy" % self.ps_default_code  # self.get_next_code('ps_default_code', self.ps_default_code)
            vals['ps_default_code'] = ps_default_code
            vals['default_code'] = default_code
        return vals_list

    def update_prestashop_quantities(self):
        """Update prestashop template quantity"""
        for template in self:
            # Recompute product template PrestaShop qty
            template.mapped("prestashop_bind_ids").sudo().recompute_prestashop_qty()
            # Recompute variant PrestaShop qty
            template.mapped(
                "product_variant_ids.prestashop_combinations_bind_ids"
            ).sudo().recompute_prestashop_qty()
        return True


class ProductQtyMixin(models.AbstractModel):
    _name = "prestashop.product.qty.mixin"
    _description = "Prestashop mixin shared between product and template"

    def manually_recompute_prestashop_qty(self):
        self.recompute_prestashop_qty(force=True)
        return True

    def recompute_prestashop_qty(self, force=False):
        """force: forcefully export qty even if there is no change in qty"""
        # group products by backend
        backends = defaultdict(set)
        for product in self:
            backends[product.backend_id].add(product.id)

        for backend, product_ids in backends.items():
            products = self.browse(product_ids)
            products._recompute_prestashop_qty_backend(backend, force=force)
        return True

    def _recompute_prestashop_qty_backend(self, backend, force=False):
        # locations = backend._get_locations_for_stock_quantities()
        # self_loc = self.with_context(location=locations.ids, compute_child=False)
        self_loc = self.with_context(warehouse=backend.warehouse_id.id, compute_child=True)

        for product_binding in self_loc:
            new_qty = product_binding._get_prestashop_qty(backend)
            if force:
                product_binding.write({'quantity': new_qty})
            elif product_binding.quantity != new_qty:
                product_binding.quantity = new_qty
        return True

    def _get_prestashop_qty(self, backend=False):
        # qty = self[backend.product_qty_field]
        # product = self.odoo_id.with_context(warehouse=self.backend_id.warehouse_id.id)
        # We are not sending the actual stock, insted we are sending the onhand qty - outgoing qty.
        # So we are sending the virtual qty(oh+in-out) - incoming
        if self.ps_type == 'virtual':
            new_qty = self.qty_available
        else:
            new_qty = self.qty_available - self.outgoing_qty
            # qty = self[backend.product_qty_field]
        if new_qty < 0:
            new_qty = 0.0
        return new_qty


class PrestashopProductTemplate(models.Model):
    _name = "prestashop.product.template"
    _inherit = [
        "prestashop.binding.odoo",
        "prestashop.product.qty.mixin",
    ]
    _inherits = {'product.template': 'odoo_id'}
    _description = "prestashop products"

    odoo_id = fields.Many2one(
        comodel_name='product.template',
        required=True,
        ondelete='cascade',
        string='Template',
    )
    ps_name = fields.Char('Prestashop Name', translate=True)

    prestashop_default_category_id = fields.Many2one(
        comodel_name='prestashop.product.category',
        string='PrestaShop Default Category',
        ondelete='set null'
    )

    prestashop_categ_ids = fields.Many2many(
        comodel_name="prestashop.product.category",
        relation="presta_product_categ_rel",
        column1="product_id",
        column2="categ_id",
        string="Extra PS categories",
        copy=False,
    )

    prestashop_tag_ids = fields.Many2many(
        comodel_name='prestashop.product.tag', relation='ps_product_tmpl_ps_tag_rel',
        column1='product_id', column2='tag_id', string='Tags', copy=True
    )
    # TODO FIXME what name give to field present in
    # prestashop_product_product and product_product
    # always_available = fields.Boolean(#not using anymore. using ps_active
    #     string='Active',
    #     default=True,
    #     help='If checked, this product is considered always available')
    ps_active = fields.Boolean("Active in PS",
                               default=True, )
    ps_active_date = fields.Datetime("Activation Date")
    quantity = fields.Float(
        string='Computed Quantity', copy=False,
        help="Last computed quantity to send to PrestaShop."
    )
    description_html = fields.Html(
        string='Description',
        translate=True,
        help="HTML description from PrestaShop",
    )
    description_short_html = fields.Html(
        string='Short Description',
        translate=True,
    )
    date_add = fields.Datetime(
        string='Created at (in PrestaShop)',
        readonly=True
    )
    date_upd = fields.Datetime(
        string='Updated at (in PrestaShop)',
        readonly=True
    )
    default_shop_id = fields.Many2one(
        comodel_name='prestashop.shop',
        string='Default shop',
        required=False
    )
    link_rewrite = fields.Char(
        string='Friendly URL',
        translate=True,
    )
    available_for_order = fields.Boolean(
        string='Available for Order Taking',
        help="Show/Hide Add to Cart button",
        default=True,
    )
    show_price = fields.Boolean(string='Display Price', default=True)
    combinations_ids = fields.One2many(
        comodel_name='prestashop.product.product',
        inverse_name='main_template_id',
        string='Combinations'
    )
    reference = fields.Char(string='Original reference')
    upc = fields.Char('UPC', copy=False)
    on_sale = fields.Boolean(string='Show on sale icon')
    wholesale_price = fields.Float(
        string='Cost Price',
        digits="Product Price",
    )
    # use_attr_from_template = fields.Boolean('Use attributes and values from template')
    # ps_attribute_line_ids = fields.One2many('prestashop.product.attribute.line','main_template_id',
    #                                         'Variants',copy=True)
    out_of_stock = fields.Selection([
        ('0', 'Refuse order'),
        ('1', 'Accept order'),
        ('2', 'Default prestashop')], default='2',
        string='If stock shortage')
    low_stock_threshold = fields.Integer()
    low_stock_alert = fields.Boolean()
    visibility = fields.Selection(
        selection=[
            ("both", "All shop"),
            ("catalog", "Only Catalog"),
            ("search", "Only search results"),
            ("none", "Hidden"),
        ],
        default="both",
    )

    @api.onchange("ps_active")
    def onchange_ps_active(self):
        if self.ps_active:
            if not self.ps_active_date:
                self.ps_active_date = fields.Datetime.now()
        else:
            self.ps_active_date = False

    @api.onchange("description_short_html")
    def description_short(self):
        if len(self.description_short_html) > 805:
            raise exceptions.ValidationError(_("Max. characters allowed is 806"))

    def copy_data(self, default=None):
        vals_list = super().copy_data(default)
        for product, vals in zip(self, vals_list):
            vals['prestashop_bind_ids'] = []
            vals['product_variant_ids'] = []
            vals['prestashop_id'] = False
            vals['quantity'] = 0
            vals['name'] = "%s (copy)" % product.name,
            vals['reference'] = "%s_copy" % product.ps_default_code
            vals['ps_name'] = "%s (Copy)" % product.ps_name
            vals['link_rewrite'] = "%s-copy" % product.link_rewrite
        return vals_list

    def import_products(self, backend, since_date=None, **kwargs):
        filters = None
        if since_date:
            filters = {'date': '1', 'filter[date_upd]': '>[%s]' % (since_date)}
        now_fmt = fields.Datetime.now()

        self.env['prestashop.product.category'].import_batch_merge(
            backend, filters=filters, priority=10)

        self.env['prestashop.product.template'].import_batch_merge(
            backend, filters=filters, priority=15)

        backend.import_products_since = now_fmt
        return True

    def import_inventory(self, backend):
        with backend.work_on("_import_stock_available") as work:
            importer = work.component(usage="batch.importer")
            return importer.run()

    def export_inventory(self, fields=None):
        """ Export the inventory configuration and quantity of a product. """
        backend = self.backend_id
        with backend.work_on('prestashop.product.template') as work:
            exporter = work.component(usage='inventory.exporter')
            return exporter.run(self, fields)

    def export_product_quantities(self, backend=None, manual_update=False):
        if not manual_update:
            self.search([('backend_id', '=', backend.id)]
                        ).recompute_prestashop_qty()
        else:
            self.search([('backend_id', '=', backend.id)]
                        ).manually_recompute_prestashop_qty()


class TemplateAdapter(Component):
    _name = 'prestashop.product.template.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.product.template'
    _prestashop_model = 'products'
    _export_node_name = 'product'
    _export_node_name_res = 'product'


class ProductTemplateBinder(Component):
    _name = 'prestashop.product.template.binder'
    _inherit = 'prestashop.binder'
    _apply_on = 'prestashop.product.template'


class ImportInventory(models.TransientModel):
    # In actual connector version is mandatory use a model
    _name = '_import_stock_available'
    _description = "PS stock transient model"

    @api.model
    def import_record(self, backend, prestashop_id, record=None, **kwargs):
        """ Import a record from PrestaShop """
        with backend.work_on(self._name) as work:
            importer = work.component(usage='prestashop.importer')
            return importer.run(prestashop_id, record=record, **kwargs)


class ProductInventoryAdapter(Component):
    _name = '_import_stock_available.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = '_import_stock_available'
    _prestashop_model = 'stock_availables'
    _export_node_name = _export_node_name_res = 'stock_available'



    def get(self, options=None):
        return self.client.get(self._prestashop_model, options=options)

    def export_quantity(self, filters, quantity):
        self.export_quantity_url(
            filters,
            quantity,
        )

        shops = self.env["prestashop.shop"].search(
            [
                ("backend_id", "=", self.backend_record.id),
                ("default_url", "!=", False),
            ]
        )
        for shop in shops:
            url = "%s/api" % shop.default_url
            key = self.backend_record.webservice_key
            client = PrestaShopWebServiceDict(url, key)
            self.export_quantity_url(filters, quantity, client=client)

    @retryable_error
    def export_quantity_url(self, filters, quantity, client=None):
        if client is None:
            client = self.client
        virtual = False
        #         if template.ps_type == 'virtual':
        #             virtual = True
        if quantity['is_virtual']:
            virtual = True
        response = client.search(self._prestashop_model, filters)
        for stock_id in response:
            res = client.get(self._prestashop_model, stock_id)
            first_key = list(res.keys())[0]
            stock = res[first_key]
            stock['quantity'] = int(quantity['quantity'])
            # stock['out_of_stock'] = int(quantity['out_of_stock'])
            if virtual:  # Do we need this
                stock['out_of_stock'] = '2'
            client.edit(self._prestashop_model, {
                self._export_node_name: stock
            })
