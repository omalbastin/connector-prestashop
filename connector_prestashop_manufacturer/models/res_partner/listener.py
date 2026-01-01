# © 2016-TODAY Omal Bastin(O4 ODOO) <omalbastin@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

_logger = logging.getLogger(__name__)

# class PartnerListener(Component):
#     _name = 'res.partner.listener'
#     _inherit = 'prestashop.connector.listener'
#     _apply_on = 'res.partner'
#     
#     @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
#     def on_record_create(self, record, fields=None):
#         """Sync partner as manufacturer.
#     
#         Sync happens only if:
#         * partner type is "supplier"
#         * PS manufacturer category is applied to it
#         """
#         ps_categ = env.ref(
#             'connector_prestashop_manufacturer.partner_manufacturer_tag')
#         if record.supplier and ps_categ.id in record.category_id.ids:
#             for backend in self.env['prestashop.backend'].search([]):
#                 backend.with_delay(priority=20).export_manufacturer(record_id, fields)
#         
#     @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
#     def on_record_write(self, record, fields=None):
#         """Sync partner as manufacturer.
#     
#         Sync happens only if:
#         * partner type is "supplier"
#         * PS manufacturer category is applied to it
#         """
#         ps_categ = env.ref(
#             'connector_prestashop_manufacturer.partner_manufacturer_tag')
#         if record.supplier and ps_categ.id in record.category_id.ids:
#             for backend in self.env['prestashop.backend'].search([]):
#                 backend.with_delay(priority=20).export_manufacturer(record_id, fields)
# 
#
