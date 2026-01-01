# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import datetime
from odoo import fields
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class MailMessageMapper(Component):
    _name = 'prestashop.mail.message.import.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.mail.message'

    direct = [
        ('message', 'body'),
    ]

    @mapping
    def message_type(self, record):
        return {'message_type': 'comment'}

    @mapping
    def data_add(self, record):
        if record['date_add'] == '0000-00-00 00:00:00':
            return {'date': fields.Datetime.now()}
        return {'date': self.backend_record.to_utc_datetime(record['date_add'])}

    @mapping
    def object_ref(self, record):
        binder = self.binder_for('prestashop.sale.order')
        order = binder.to_internal(record['id_order'], unwrap=True)
        return {
            'model': 'sale.order',
            'res_id': order.id,
        }

    @mapping
    def author_id(self, record):
        if record['id_customer'] != '0':
            binder = self.binder_for('prestashop.res.partner')
            partner = binder.to_internal(record['id_customer'], unwrap=True)
            return {'author_id': partner.id}
        return {}


class MailMessageOtherMapper(Component):
    _name = 'prestashop.mail.message.other.import.mapper'
    _inherit = 'prestashop.import.mapper'
    _apply_on = 'prestashop.mail.message.other'

    direct = [
        ('message', 'body'),
    ]

    @mapping
    def message_type(self, record):
        return {'message_type': 'comment'}

    @mapping
    def data_add(self, record):
        if record['date_add'] == '0000-00-00 00:00:00':
            return {'date': fields.Datetime.now()}
        return {'date': self.backend_record.to_utc_datetime(record['date_add'])}

    @mapping
    def object_ref(self, record):
        binder = self.binder_for('prestashop.sale.order')
        order = binder.to_internal(record['id_order'], unwrap=True)
        return {
            'model': 'sale.order',
            'res_id': order.id,
        }

    @mapping
    def author_id(self, record):
        if record['id_customer'] != '0':
            binder = self.binder_for('prestashop.res.partner')
            partner = binder.to_internal(record['id_customer'], unwrap=True)
            return {'author_id': partner.id}
        return {}


#     @mapping
#     def order_related(self, record):
#         so_binder = self.binder_for('prestashop.sale.order')
# #         adapter = self.unit_for(GenericAdapter, '_customer_threads')
#         res = {}
#         if record['id_order']:
#             order = so_binder.to_internal(record['id_order'], unwrap=True)
#             res.update({
#                 'model': 'sale.order',
#                 'res_id': order.id,
#             })
#             if record['id_customer'] != '0':
#                 partner_binder = self.binder_for('prestashop.res.partner')
#                 partner = partner_binder.to_internal(record['id_customer'], unwrap=True)
#                 res.update({'author_id': partner.id})
#              
#         return res

class MailMessageImporter(Component):
    """ Import one simple record """
    _name = 'prestashop.mail.message.importer'
    _inherit = 'prestashop.importer'
    _apply_on = 'prestashop.mail.message'

    def _import_dependencies(self):
        record = self.prestashop_record
        if record['id_order'] != '0':
            self._import_dependency(record['id_order'], 'prestashop.sale.order', importer_usage='prestashop.importer')
        if record['id_customer'] != '0':
            self._import_dependency(
                record['id_customer'], 'prestashop.res.partner'
            )

    def _has_to_skip(self, binding=False):
        record = self.prestashop_record
        if not record.get('id_order') or record["id_order"] == "0":
            return 'skipped: no id_order'
        binder = self.binder_for('prestashop.sale.order')
        order_binding = binder.to_internal(record['id_order'])
        if not order_binding:
            return 'skipped: no order binding'


class MailMessageOtherImporter(Component):
    """ Import one simple record """
    _name = 'prestashop.mail.message.other.importer'
    _inherit = 'prestashop.importer'
    _apply_on = 'prestashop.mail.message.other'

    def _import_dependencies(self):
        record = self.prestashop_record
        if record['id_order'] != '0':
            self._import_dependency(record['id_order'], 'prestashop.sale.order', importer_usage='prestashop.importer')
        if record['id_customer'] != '0':
            self._import_dependency(
                record['id_customer'], 'prestashop.res.partner'
            )

    def _has_to_skip(self, binding=False):
        record = self.prestashop_record
        if not record.get('id_order') or record['id_order'] == '0':
            return 'skipped: no id_order'
        binder = self.binder_for('prestashop.sale.order')
        order_binding = binder.to_internal(record['id_order'])
        if not order_binding:
            return 'skipped: no order binding'


class MailMessageBatchImporter(Component):
    _name = 'prestashop.mail.message.batch.importer'
    _inherit = 'prestashop.batch.importer'
    _apply_on = 'prestashop.mail.message'


class MailMessageMatchImporter(Component):
    _name = 'prestashop.mail.message.match.importer'
    _inherit = 'prestashop.match.importer'
    _apply_on = 'prestashop.mail.message'


class MailMessageMatchBatchImporter(Component):
    _name = 'prestashop.mail.message.batch.match.importer'
    _inherit = 'prestashop.batch.match.importer'
    _apply_on = 'prestashop.mail.message'


class MailMessageOtherBatchImporter(Component):
    _name = 'prestashop.mail.message.other.batch.importer'
    _inherit = 'prestashop.batch.importer'
    _apply_on = 'prestashop.mail.message.other'


class MailMessageOtherMatchImporter(Component):
    _name = 'prestashop.mail.message.other.match.importer'
    _inherit = 'prestashop.match.importer'
    _apply_on = 'prestashop.mail.message.other'


class MailMessageOtherMatchBatchImporter(Component):
    _name = 'prestashop.mail.message.other.match.batch.importer'
    _inherit = 'prestashop.batch.match.importer'
    _apply_on = 'prestashop.mail.message.other'
