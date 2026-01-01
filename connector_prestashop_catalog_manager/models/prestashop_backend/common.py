# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# © 2016-TODAY Omal Bastin(O4 ODOO) <omalbastin@gmail.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import models, fields, api


class PrestashopBackend(models.Model):
    _inherit = 'prestashop.backend'

    exclude_export_template_ids = fields.Many2many('product.template',
                                                   'exclude_product_rel', 'b_id', 'pt_id',
                                                   'Export Excluded Products')


    # def synchronize_basedata(self):
    #     res = super().synchronize_basedata()
    #     # self.ensure_one()
    #     # res=True
    #     # self.with_delay(priority=5).import_batch_merge('prestashop.product.attribute')
    #     # self.with_delay(priority=10).import_batch_merge('prestashop.product.attribute.value')
    #     # self.with_delay(priority=5).import_batch_merge('prestashop.product.feature')
    #     # self.with_delay(priority=6).import_batch_merge('prestashop.product.feature.value')
    #     return res

    def import_existing_categs(self):
        self.ensure_one()
        for binding in self.env['prestashop.product.category'].search([('backend_id', '=', self.id)]):
            binding.with_context(connector_delay=True).resync()

    def export_all_categs(self):
        """ Export categ on PrestaShop """
        for backend_record in self:
            for binding in self.env['prestashop.product.category'].search([('backend_id', '=', backend_record.id)]):
                binding.with_context(connector_delay=True).re_export()
        return True

    def export_all_attribute(self):
        """ Export products on PrestaShop """
        # TODO: FIX PRESTASHOP do not support partial edit
        for backend_record in self:
            for binding in self.env['prestashop.product.attribute'].search([('backend_id', '=', backend_record.id)]):
                binding.with_context(connector_delay=True).re_export()
            for binding in self.env['prestashop.product.attribute.value'].search(
                    [('backend_id', '=', backend_record.id)]):
                binding.with_context(connector_delay=True).re_export()
        return True

