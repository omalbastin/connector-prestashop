# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import datetime
from odoo import fields

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class PartnerCategoryImportMapper(Component):
    _name = 'prestashop.res.partner.category.import.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.res.partner.category'

    direct = [
        ('name', 'name'),
    ]

    @mapping
    def data_add(self, record):
        if record['date_add'] == '0000-00-00 00:00:00':
            return {'date_add': fields.Datetime.now()}
        return {'date_add': self.backend_record.to_utc_datetime(record['date_add'])}

    @mapping
    def data_upd(self, record):
        if record['date_upd'] == '0000-00-00 00:00:00':
            return {'date_upd': fields.Datetime.now()}
        return {'date_upd': self.backend_record.to_utc_datetime(record['date_upd'])}


class PartnerCategoryImporter(Component):
    """ Import one translatable record """
    _name = 'prestashop.res.partner.category.importer'
    _inherit = 'prestashop.translatable.importer'
    _apply_on = 'prestashop.res.partner.category'

    _translatable_fields = ['name']

    def _after_import(self, binding):
        super()._after_import(binding)
        record = self.prestashop_record
        if float(record['reduction']):
            self.env['prestashop.groups.pricelist'].import_record_merge(
                self.backend_record,
                record['id']
            )


class PartnerCategoryMatchImporter(Component):
    _name = 'prestashop.res.partner.category.match.importer'
    _inherit = 'prestashop.match.importer'
    _apply_on = 'prestashop.res.partner.category'


class PartnerCategoryBatchImporter(Component):
    _name = 'prestashop.res.partner.category.batch.importer'
    _inherit = 'prestashop.batch.importer'
    _apply_on = 'prestashop.res.partner.category'


class PartnerCategoryMatchBatchImporter(Component):
    _name = 'prestashop.res.partner.category.match.batch.importer'
    _inherit = 'prestashop.batch.match.importer'
    _apply_on = 'prestashop.res.partner.category'
