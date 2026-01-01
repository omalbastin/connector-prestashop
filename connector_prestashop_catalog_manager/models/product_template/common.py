# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# © 2016-TODAY Omal Bastin(O4 ODOO) <omalbastin@gmail.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import models, fields, api, exceptions, _

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def copy(self, default=None):
        self_context = self.with_context(connector_no_export=True)
        return super(ProductTemplate, self_context).copy(default=default)

    @api.onchange('ps_default_code')
    def onchange_ps_default_code(self):
        if self.ps_default_code:  # and not self.default_code:
            binding_data = []
            for binding in self.prestashop_bind_ids:
                f = binding.backend_id.product_merge_based_on
                setattr(binding, f, self.ps_default_code)
                # binding_f = self.ps_default_code
            #     binding_data.append(
            #         (1, binding.id, {f: self.ps_default_code}))
            # self.prestashop_bind_ids = binding_data
            if len(self.product_variant_ids) == 1:
                self.product_variant_ids.default_code = self.ps_default_code
            #             if not self.default_code:
            self.default_code = self.ps_default_code

    def toggle_active(self):
        ps_bind_ids = self.with_context(active_test=False).prestashop_bind_ids
        super().toggle_active()
        for backend in ps_bind_ids:
            record = backend.odoo_id
            if record.active:
                record.ps_active = True
                record.ps_active_date = fields.Datetime.now()
                # backend.always_available = True
                backend.available_for_order = True
            else:
                record.ps_active = False
                record.ps_active_date = False
                # backend.always_available = False
                backend.available_for_order = False
    @api.model
    def scheduler_deactivate_default_product(self):
        for template in self.search([]):
            if template.product_variant_count != 1:
                for product in template.product_variant_ids:
                    if not product.product_template_attribute_value_ids:
                        self.env['product.product'].browse(product.id).write(
                            {'active': False})


    @api.onchange('ps_default_code')
    def onchange_ps_default_code(self):
        if self.ps_default_code:  # and not self.default_code:

            binding_data = []
            for binding in self.prestashop_bind_ids:
                binding_data.append(
                    (1, binding.id, {'reference': self.ps_default_code}))
            self.prestashop_bind_ids = binding_data
            if len(self.product_variant_ids) == 1:
                self.product_variant_ids.default_code = self.ps_default_code
            #             if not self.default_code:
            self.default_code = self.ps_default_code

    def create_ps_records(self):
        """Check and create products to backends"""
        backend_objs = self.env['prestashop.backend'].sudo().search([])
        for template in self.sudo():
            if not template.active:
                continue
            # if not template.ps_active:
            #     continue
            if not template.ps_default_code:
                raise exceptions.UserError(_('Please specify Prestashop default code'))
            existing_backend_ids = template.prestashop_bind_ids.mapped('backend_id.id')
            for backend in backend_objs:
                if backend.id in existing_backend_ids:
                    continue
                f = backend.product_merge_based_on
                #                 categ_id = self.env['prestashop.product.category'].search([('backend_id','=',backend.id),
                #                                                               ('prestashop_id','!=',1)],limit=1)
                ps_binding = self.env['prestashop.product.template'].sudo().create({
                    'odoo_id': template.id,
                    'backend_id': backend.id,
                    'ps_name': template.name,
                    'ps_active': True,
                    'ps_active_date': fields.Datetime.now(),
                    f: template.ps_default_code,
                    'link_rewrite': backend.get_slug(template.name),
                    #                     'categ_id':categ_id.odoo_id.id,
                    #                     'categ_ids':[(6,0,[categ_id.odoo_id.id])]
                })
            if template.virtual_available:
                template.with_delay().update_prestashop_quantities()
        return True


class PrestashopProductTemplate(models.Model):
    _inherit = 'prestashop.product.template'

    meta_title = fields.Char(
        string='Meta Title',
        translate=True
    )
    meta_description = fields.Char(
        string='Meta Description', size=160,
        translate=True
    )
    meta_keywords = fields.Char(
        string='Meta Keywords',
        translate=True
    )

    online_only = fields.Boolean(string='Online Only')
    additional_shipping_cost = fields.Float(
        string='Additional Shipping Price',
        digits='Product Price',
        help="Additional Shipping Price for the product on Prestashop")
    available_now = fields.Char(
        string='Available Now',
        translate=True
    )
    available_later = fields.Char(
        string='Available Later',
        translate=True
    )
    available_date = fields.Date(string='Available From')
    minimal_quantity = fields.Integer(
        string='Minimal Quantity',
        help='Minimal Sale quantity',
        default=1,
    )
    # feature_line_ids = fields.One2many('prestashop.product.feature.line','main_template_id',
    #                                    'Features', copy=False)#not using anymore june 17 2020

    ps_state = fields.Integer('PS State', default=1)


    def copy_data(self, default=None):
        vals_list = super().copy_data(default)
        for product, vals in zip(self, vals_list):
            vals['product_tag_ids'] = []
        return vals_list

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('prestashop_id', 'ilike', name)] + args, limit=limit)
        if not recs:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()