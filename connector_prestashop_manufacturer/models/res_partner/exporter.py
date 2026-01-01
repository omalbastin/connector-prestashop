# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import _
from odoo.addons.component.core import AbstractComponent, Component
from odoo.addons.connector.components.mapper import mapping

_logger = logging.getLogger(__name__)
try:
    from odoo.addons.connector_prestashop.prestapyt import PrestaShopWebServiceError
except:
    _logger.debug('Cannot import from `prestapyt`')


class ExporterMixin(AbstractComponent):
    _name = 'prestashop.exporter.mixin'
    _inherit = 'prestashop.exporter'

    def run(self, binding_id, *args, **kwargs):
        try:
            super(ExporterMixin, self).run(binding_id, **kwargs)
        except PrestaShopWebServiceError as error:
            self._handle_ws_error(binding_id, error, **kwargs)

    def _handle_ws_error(self, binding_id, error, **kwargs):
        binder = self.binder_for(self._model_name)
        manuf = binder.to_internal(binding_id, unwrap=True)
        msg = _(
            'Export of %s failed. Error: %s.'
        ) % (self.msg_model_name, error.ps_error_msg)
        self.backend_record.add_checkpoint(
            manuf,
            message=msg,
        )


class ManufacturerExporter(Component):
    _name = 'prestashop.manufacturer.exporter'
    _inherit = 'prestashop.exporter.mixin'
    _apply_on = 'prestashop.manufacturer'

    msg_model_name = 'Manufacturer'

    def _export_addresses(self):
        partner_record = self.binding.odoo_id
        addresses = partner_record.child_ids  # or [partner_record, ]
        for address in addresses:
            self._export_dependency(
                address,
                'prestashop.manufacturer.address',
                bind_values={'prestashop_partner_id': self.binding.id},
                force_sync=True)

    def _after_export(self):
        super(ManufacturerExporter, self)._export_dependencies()
        self._export_addresses()


class ManufacturerExportMapper(Component):
    _name = 'prestashop.manufacturer.export.mapper'
    _inherit = 'prestashop.export.mapper'
    _apply_on = 'prestashop.manufacturer'

    direct = [
        ('name', 'name'),
    ]

    @mapping
    def active(self, record):
        return {'active': record['active_ext'] and '1' or '0'}


class ManufacturerAddressExporter(Component):
    _name = 'prestashop.manufacturer.address.exporter'
    _inherit = 'prestashop.exporter.mixin'
    _apply_on = 'prestashop.manufacturer.address'

    msg_model_name = 'Manufacturer Address'


class AddressExportMapper(Component):
    _name = 'prestashop.manufacturer.address.export.mapper'
    _inherit = 'prestashop.export.mapper'
    _apply_on = 'prestashop.manufacturer.address'

    direct = [
        # `alias` in PS is a label for the address and is required
        ('type', 'alias'),
        ('street', 'address1'),
        ('street2', 'address2'),
        ('city', 'city'),
        ('comment', 'other'),
        ('phone', 'phone'),
        ('mobile', 'phone_mobile'),
        ('zip', 'postcode'),
        # (m2o_to_backend('prestashop_partner_id'), 'id_manufacturer'),
    ]

    @mapping
    def name(self, record):
        # TODO: use partner 1st name last name module (?)
        partner = record.prestashop_partner_id
        parts = [
            x.strip().capitalize()
            for x in partner.display_name.split(' ') if x.strip()
        ]
        first = ' '.join(parts[:1])
        last = ' '.join(parts[1:]).strip() or first  # can't be null
        return {
            'firstname': first,
            'lastname': last,
        }

    @mapping
    def country(self, record):
        if record.country_id:
            binder = self.binder_for('prestashop.res.country')
            country_id = binder.to_external(record.country_id.id, wrap=1)
            return {'id_country': country_id}
        return {}

    @mapping
    def manufacturer(self, record):
        binder = self.binder_for('prestashop.manufacturer')
        value = binder.to_external(record.prestashop_partner_id.id)
        if value:
            return {'id_manufacturer': value}
        return {}
