# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class ProductTagExporter(Component):
    _name = 'prestashop.product.tag.exporter'
    _inherit = 'prestashop.exporter'
    _apply_on = 'prestashop.product.tag'


#     def _create(self, record):
#         res = super(ProductTagExporter, self)._create(record)
#         return res['prestashop']['tag']['id']
# 
#     def _update(self, record):
#         res = super(ProductTagExporter, self)._update(record)
#         return res['prestashop']['tag']['id']


class ProductTagExportMapper(Component):
    _name = 'prestashop.product.tag.export.mapper'
    _inherit = 'translation.prestashop.export.mapper'
    _apply_on = 'prestashop.product.tag'

    direct = [
        ('name', 'name'),
        ('ps_lang_id', 'id_lang')
    ]
    # handled by base mapping `translatable_fields`
    _translatable_fields = [
        ('name', 'name')
    ]
