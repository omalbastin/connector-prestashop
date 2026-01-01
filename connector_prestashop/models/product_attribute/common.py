# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models

from odoo.addons.component.core import Component


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.attribute',
        inverse_name='odoo_id',
        string='PrestaShop Bindings (Attributes)',
    )


class PrestashopProductCombinationOption(models.Model):
    _name = 'prestashop.product.attribute'
    _inherit = 'prestashop.binding.odoo'
    _inherits = {'product.attribute': 'odoo_id'}
    _description = "Product combination option prestashop bindings: product_options"

    odoo_id = fields.Many2one(
        comodel_name='product.attribute',
        string='Attribute',
        required=True,
        ondelete='cascade',
    )
    prestashop_position = fields.Integer('PrestaShop Position')
    group_type = fields.Selection([
        ('color', 'Color'),
        ('radio', 'Radio'),
        ('select', 'Select')], string='Type', default='select')
    public_name = fields.Char(string='Public Name', translate=True)


class ProductCombinationOptionAdapter(Component):
    _name = 'prestashop.product.attribute.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.product.attribute'

    _prestashop_model = 'product_options'
    _export_node_name = 'product_options'


class ProductAttributeBinder(Component):
    _name = 'prestashop.product.attribute.binder'
    _inherit = 'prestashop.binder'
    _apply_on = 'prestashop.product.attribute'


class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.product.attribute.value',
        inverse_name='odoo_id',
        string='PrestaShop Bindings',
    )


class PrestashopProductAttributeValue(models.Model):
    _name = 'prestashop.product.attribute.value'
    _inherit = 'prestashop.binding'
    _inherits = {'product.attribute.value': 'odoo_id'}
    _description = "Product option value prestashop bindings: product_option_values"

    odoo_id = fields.Many2one(
        comodel_name='product.attribute.value',
        string='Attribute',
        required=True,
        ondelete='cascade',
    )
    prestashop_position = fields.Integer(
        string='PrestaShop Position',
        default=1,
    )
    id_attribute_group = fields.Many2one(
        comodel_name='prestashop.product.attribute')


class ProductAttributeValueAdapter(Component):
    _name = 'prestashop.product.attribute.value.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.product.attribute.value'

    _prestashop_model = 'product_option_values'
    _export_node_name = _export_node_name_res = 'product_option_value'


class ProductAttributeValueBinder(Component):
    _name = 'prestashop.product.attribute.value.binder'
    _inherit = 'prestashop.binder'
    _apply_on = 'prestashop.product.attribute.value'
