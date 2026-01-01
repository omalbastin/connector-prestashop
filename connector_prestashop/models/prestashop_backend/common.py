# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime
import logging
import pytz
import re
import unicodedata

from odoo import models, fields, api, exceptions, _
from odoo.addons.base.models.res_partner import _tz_get
from odoo.addons.component.core import Component
from odoo.addons.queue_job.job import identity_exact
from ...components.backend_adapter import api_handle_errors

try:
    import slugify as slugify_lib
except ImportError:
    slugify_lib = None

_logger = logging.getLogger(__name__)


class PrestashopBackend(models.Model):
    _name = 'prestashop.backend'
    _description = 'PrestaShop Backend Configuration'
    _inherit = 'connector.backend'

    _versions = {
        '1.5': 'prestashop.version.key',
        '1.6.0.9': 'prestashop.version.key.1.6.0.9',
        '1.6.0.11': 'prestashop.version.key.1.6.0.9',
        '1.6.1.2': 'prestashop.version.key.1.6.1.2',
        '1.7.4.2': 'prestashop.version.key.1.7.4.2',
        '8.1': 'prestashop.version.key.8.1',
    }

    @api.model
    def _lang_get(self):
        return self.env['res.lang'].get_installed()

    def _select_versions(self):
        """ Available versions

        Can be inherited to add custom versions.
        """
        return [
            ('1.5', '< 1.6.0.9'),
            ('1.6.0.9', '1.6.0.9 - 1.6.0.10'),
            ('1.6.0.11', '>= 1.6.0.11 - <1.6.1.2'),
            ('1.6.1.2', '>=1.6.1.2 - <1.6.9'),
            ('1.7.4.2', '>=1.7 - < 8.0'),
            ('8.1', '>=8.1.0')

        ]

    @api.model
    def _select_state(self):
        """Available States for this Backend"""
        return [
            ("draft", "Draft"),
            ("checked", "Checked"),
            ("production", "In Production"),
        ]

    @api.model
    def _get_ps_model_selection(self):
        excluded_models = [
            "prestashop.binding",
            "prestashop.binding.odoo",
            "prestashop.backend",
        ]
        prestashop_models = self.env["ir.model"].search_read(
            [("model", "ilike", "prestashop.%")], ["model"]
        )
        return [
            (x["model"], x["model"])
            for x in prestashop_models
            if x["model"] not in excluded_models
                           ]

    @api.model
    def _default_warehouse_id(self):
        # companies = self.company_id or self.env.company
        return self.env.user._get_default_warehouse_id()

    @api.model
    def _default_pricelist_id(self):
        return self.env["product.pricelist"].search([], limit=1)

    name = fields.Char(string="Name", required=True)
    version = fields.Selection(
        selection='_select_versions',
        string='Version',
        required=True,
    )
    location = fields.Char('Location')
    webservice_key = fields.Char(
        string='Webservice key',
        help="You have to put it in 'username' of the PrestaShop "
             "Webservice api path invite"
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        required=True,
        help='Warehouse used to compute the stock quantities.'
    )
    stock_location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Stock Location',
        help='Location used to import stock quantities.'
    )
    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist',
        required=False,
        default=lambda self: self._default_pricelist_id(),
        help="Pricelist used in sales orders",
    )
    sale_team_id = fields.Many2one(
        comodel_name='crm.team',
        string='Sales Team',
        help="Sales Team assigned to the imported sales orders.",
    )

    refund_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Refund Journal',
    )

    # old_table_id = fields.Integer(string='Old Table ID')
    taxes_included = fields.Boolean("Use tax included prices")
    import_partners_since = fields.Datetime('Import partners since')
    import_orders_since = fields.Datetime('Import Orders since')
    import_payment_mode_since = fields.Datetime("Import Payment Modes since")
    import_products_since = fields.Datetime('Import Products since')
    import_refunds_since = fields.Datetime('Import Refunds since')
    import_suppliers_since = fields.Datetime('Import Suppliers since')
    specific_model_name = fields.Selection('_get_ps_model_selection', 'Model')
    specific_record_id = fields.Char('PS Record ID')
    language_ids = fields.One2many(
        comodel_name='prestashop.res.lang',
        inverse_name='backend_id',
        string='Languages',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        index=True,
        required=True,
        default=lambda self: self.env.company,
        string='Company',
    )
    discount_product_id = fields.Many2one(
        comodel_name='product.product',
        index=True,
        required=True,
        string='Discount Product',
    )
    shipping_product_id = fields.Many2one(
        comodel_name='product.product',
        index=True,
        required=True,
        string='Shipping Product',
    )

    so_prefix_code = fields.Char('Order Prefix Code')
    product_merge_based_on = fields.Selection([('reference', 'Reference'), ('upc', 'UPC')],
                                              'Product Merge Based on', default="reference", )
    # import_export_images = fields.Selection([('import', 'Import Only'),
    #                                          ('export', 'Export Only'),
    #                                          ('import_export', 'Import and Export')],
    #                                         'Product Images', default='export')
    auto_update_stock = fields.Boolean(
        string='Export Stock Values?',
        help="If set, product stock details will be exported even if 'Update to PS' is inactive")
    use_dummy_product = fields.Boolean('Use Dummy Product in Sale Order',
                                       help="If no related product is found "
                                            "for a Sale Order line, use the dummy Product")
    dummy_product_id = fields.Many2one('product.product', 'Dummy Product',
                                       # default=lambda s:s.env.ref('connector_prestashop.product_dummy')
                                       )
    importable_order_state_ids = fields.Many2many(
        comodel_name='sale.order.state',
        string='Importable sale order states',
        help="If valued only orders matching these states will be imported.",
    )
    active = fields.Boolean('Active', default=True)
    state = fields.Selection(selection="_select_state", default="draft")

    verbose = fields.Boolean(help="Output requests details in the logs")
    debug = fields.Boolean(help="Activate PrestaShop's webservice debug mode")
    tz = fields.Selection(
        _tz_get, 'Timezone', default=lambda self: self._context.get('tz'),
        help="The timezone of the backend. Used to synchronize the sale order "
             "date.")
    export_active = fields.Boolean(
        string='Update to PS?', default=False,
    )
    product_qty_field = fields.Selection(
        selection=[
            ("qty_available_not_res", "Immediately usable qty"),
            ("qty_available", "Qty available"),
        ],
        string="Product qty",
        help="Select how you want to calculate the qty to push to PS. ",
        default="qty_available",
        required=True,
    )
    default_language = fields.Selection(_lang_get, string='Default Language',
                                        # default=lambda self: self.env.user.lang,
                                        help="If prestashop have multiple languages, "
                                             "data related to this language will be imported first")

    def generate_identity_key(self, binding=None, model_ps_id=None):
        minute_window = fields.Datetime.now().minute // 2
        if binding:
            identity = f"{self.id}{binding._name}({binding.id})-w{minute_window}"
        elif model_ps_id:
            identity = f"{self.id}{model_ps_id})-w{minute_window}"
        return identity

    @api.model
    def to_utc_datetime(self, datetime_str):
        """Returns the given timestamp converted to the utc's timezone. Used while importing records

           :param datetime string: datetime value to be converted to the utc timezone
           :rtype: string
           :return: datetime string converted to timezone-aware datetime in utc
                    timezone
        """
        tz_name = self.tz or self.env.user.tz or self._context.get('tz') or 'UTC'
        local = pytz.timezone(tz_name)
        local_dt = local.localize(fields.Datetime.from_string(datetime_str), is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)

        return fields.Datetime.to_string(utc_dt)

    def get_slug(self, strings):
        if slugify_lib:
            try:
                strings = strings
                return slugify_lib.slugify(strings)
            except TypeError:
                pass
        uni = unicodedata.normalize('NFKD', strings).encode(  # strings.decode('utf-8')
            'ascii', 'ignore').decode('ascii')
        slug = re.sub(r'[\W_]', ' ', uni).strip().lower()
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug

    def is_slugified(self, url):
        """
        Check whether a URL is slugified based on common conventions.

        Args:
            url (str): The URL to check.

        Returns:
            bool: True if the URL is slugified, False otherwise.
        """
        # Check for hyphens instead of spaces
        if ' ' in url:
            return False

        # Check for lowercase letters
        if not url.islower():
            return False

        # Check for special characters other than hyphens
        if any(c.isalnum() or c == '-' for c in url):
            return True
        else:
            return False

    @api.constrains("product_qty_field")
    def check_product_qty_field_dependencies_installed(self):
        for backend in self:
            # we only support stock_available_unreserved module for now.
            # In order to support stock_available_immediately or
            # virtual_available for example, we would need to recompute
            # the prestashop qty at stock move level, it can't work to
            # recompute it only at quant level, like it is done today
            if backend.product_qty_field == "qty_available_not_res":
                module = (
                    self.env["ir.module.module"]
                    .sudo()
                    .search([("name", "=", "stock_available_unreserved")], limit=1)
                )
                if not module or module.state != "installed":
                    raise exceptions.UserError(
                        _(
                            "In order to choose this option, you have to "
                            "install the module stock_available_unreserved."
                        )
                    )

    def add_checkpoint(self, record, message=""):
        """
        @param record: the browse record that the checkpoint is created
        @param message: additional message to be posted in the checkpoint
        checkpoint has been removed. replaced with activities
        https://github.com/OCA/connector/issues/351
        """
        return True
        # self.ensure_one()
        # record.ensure_one()
        # checkpoint_model = self.env["connector.checkpoint"]
        # chk_point = checkpoint_model.create_from_name(
        #     record._name, record.id, self._name, self.id
        # )
        # if message:
        #     chk_point.message_post(body=message)
        # return chk_point

    @api.model
    def _default_pricelist_id(self):
        return self.env['product.pricelist'].search([], limit=1)

    def button_reset_to_draft(self):
        self.ensure_one()
        self.write({"state": "draft"})

    @api.onchange('warehouse_id')
    def onchange_warehouse_id(self):
        if self.warehouse_id:
            self.stock_location_id = self.warehouse_id.lot_stock_id.id

    def synchronize_metadata(self):
        self.ensure_one()
        # stock_location = self.stock_location_id or self.warehouse_id.lot_stock_id
        # if not stock_location.prestashop_synchronized:
        #     stock_location.write({'prestashop_synchronized': True})
        #
        for model_name in [
            'prestashop.shop.group',
            'prestashop.shop'
        ]:
            # import directly, do not delay because this
            # is a fast operation, a direct return is fine
            # and it is simpler to import them sequentially
            self.env[model_name].import_batch(self)

        for model_name in ['prestashop.res.lang']:
            # import directly to a matching record, do not delay because this
            # is a fast operation, a direct return is fine
            # and it is simpler to import them sequentially
            filters = None
            self.env[model_name].import_batch_merge(self, filters)

        return True

    def get_base_sync_models(self):
        return [

            'prestashop.res.country',
            'prestashop.res.currency',
            'prestashop.account.tax',
            'prestashop.account.tax.group',
            'prestashop.sale.order.state'

        ]

    def synchronize_basedata(self):
        self.ensure_one()
        for model_name in self.get_base_sync_models():
            filters = None
            self.env[model_name].import_batch_merge(self, filters)

        return True

    def _check_connection(self):
        self.ensure_one()
        with self.work_on('prestashop.backend') as work:
            component = work.component_by_name(name='prestashop.adapter.test')
            with api_handle_errors('Connection failed'):
                component.head()

    def button_check_connection(self):
        self._check_connection()
        # raise exceptions.UserError(_('Connection successful'))
        self.write({"state": "checked"})

    def button_reset_to_draft(self):
        self.ensure_one()
        self.write({"state": "draft"})

    def button_set_to_production(self):
        self.ensure_one()
        self.write({"state": "production"})

    def import_specific_record(self):
        self.ensure_one()
        if not self.specific_model_name:
            raise exceptions.UserError(_('Please specify Binding Model'))
        if not self.specific_record_id:
            self.import_specific_batch()
        else:
            if ',' in self.specific_record_id:
                for sid in self.specific_record_id.split(','):
                    self.env[self.specific_model_name].with_delay(
                        description=f"Specific Import {self.specific_model_name} with ID {eval(sid)}",
                        identity_key=identity_exact,
                        channel="root.prestashop_import").import_record_merge(
                        self, eval(sid)
                    )
            else:
                self.env[self.specific_model_name].with_delay(
                    description=f"Specific Import {self.specific_model_name} with ID {self.specific_record_id}",
                    identity_key=identity_exact,
                    channel="root.prestashop_import").import_record_merge(
                    self, self.specific_record_id
                )

        return True

    def import_specific_batch(self, filters=None):
        self.ensure_one()
        return self.env[self.specific_model_name].with_delay(
            channel="root.prestashop_import",
            description=f"specific Batch match import {self.specific_model_name} with filters {filters}",
        ).import_batch_merge(self, filters=filters)

    def import_customers_since(self):
        self.ensure_one()
        since_date = self.import_partners_since
        if not since_date:
            raise exceptions.UserError(_("Please provide a date"))
        self.env["prestashop.res.partner"].with_delay(
            description=f"Import customers since {since_date}",
            channel="root.prestashop_import").import_customers_since(
            backend_record=self, since_date=since_date)
        return True

    def import_products(self):
        self.ensure_one()
        since_date = self.import_products_since
        if not since_date:
            raise exceptions.UserError(_("Please provide a date"))
        self.env["prestashop.product.template"].with_delay(
            description=f"Import products since {since_date}",
            channel="root.prestashop_import").import_products(
            self, since_date
        )
        return True

    def import_carriers(self):
        self.ensure_one()
        self.env["prestashop.delivery.carrier"].with_delay(
            channel="root.prestashop_import",
            description=f"Prepare Batch import on carriers",
        ).import_batch(self)
        return True

    def update_product_stock_qty(self):
        self.ensure_one()
        manual_update = False
        if self.env.context.get('manual_update'):
            manual_update = True
        self.env["prestashop.product.template"].with_delay(
            description=f"Exporting product stock quantity",
            channel="root.prestashop_export").export_product_quantities(
            backend=self, manual_update=manual_update
        )
        self.env["prestashop.product.product"].with_delay(
            description=f"Exporting combination stock quantity",
            channel="root.prestashop_export").export_product_quantities(
            backend=self, manual_update=manual_update
        )

        return True

    def import_stock_qty(self):
        self.ensure_one()
        self.env["_import_stock_available"].with_delay(
            channel="root.prestashop_import",
            description=f"Stock batch import",
        ).import_batch(self, filters=None)

    def import_sale_orders(self):
        self.ensure_one()
        since_date = self.import_orders_since
        if not since_date:
            raise exceptions.UserError(_("Please provide a date"))
        self.env["prestashop.sale.order"].with_delay(
            channel="root.prestashop_import").import_orders_since(
            self, since_date
        )
        return True

    def import_payment_modes(self):
        self.ensure_one()
        now_fmt = fields.Datetime.now()

        since_date = self.import_payment_mode_since
        filters = {}
        if since_date:
            filters = {"date": "1", "filter[date_upd]": ">[%s]" % since_date}
        with self.work_on("account.payment.method.line") as work:
            importer = work.component(usage="prestashop.batch.importer")
            importer.run(filters=filters)
        self.import_payment_mode_since = now_fmt
        return True

    def import_refunds(self):
        self.ensure_one()
        since_date = self.import_refunds_since
        self.env['prestashop.refund'].import_refunds(
            self, since_date)
        return True

    def import_suppliers(self):
        self.ensure_one()
        since_date = self.import_suppliers_since
        self.env['prestashop.supplier'].import_suppliers(
            self, since_date)
        return True

    def get_version_ps_key(self, key):
        self.ensure_one()
        with self.work_on('_prestashop.version.key') as work:
            keys = work.component(usage=self._versions[self.version])
            return keys.get_key(key)

    def _scheduler_update_product_stock_qty(self, domain=None):
        self.search(domain or []).update_product_stock_qty()

    @api.model
    def _scheduler_import_refunds(self, domain=None):
        self.search(domain or []).import_refunds()

    @api.model
    def _scheduler_import_sale_orders(self, domain=None):
        for backend in self.search(domain or []):
            backend.import_sale_orders()

    @api.model
    def _scheduler_import_customers(self, domain=None):
        for backend in self.search(domain or []):
            backend.import_customers_since()

    @api.model
    def _scheduler_import_products(self, domain=None):
        for backend in self.search(domain or []):
            backend.import_products()

    @api.model
    def _scheduler_import_carriers(self, domain=None):
        for backend in self.search(domain or []):
            backend.import_carriers()

    @api.model
    def _scheduler_import_payment_methods(self, domain=None):
        backends = self.search(domain or [])
        for backend in backends:
            backend.import_payment_methods()

    #         backends.import_refunds()

    @api.model
    def _scheduler_restart_started_queue(self, domain=None):

        jobs = self.env['queue.job'].search([('state', 'in', ['started', 'enqueue'])])
        jobs.requeue()

    @api.model
    def _scheduler_import_suppliers(self, domain=None):
        for backend in self.search(domain or []):
            backend.import_suppliers()


class NoModelAdapter(Component):
    """ Used to test the connection """
    _name = 'prestashop.adapter.test'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.backend'
    _prestashop_model = ''
