# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo import models, fields, api, _
from odoo.addons.connector.exception import RetryableJobError, JobError
from odoo.addons.queue_job.job import identity_exact

from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PrestashopBinding(models.AbstractModel):
    _name = 'prestashop.binding'
    _inherit = 'external.binding'
    _description = 'PrestaShop Binding (abstract)'

    # 'odoo_id': openerp-side id must be declared in concrete model
    backend_id = fields.Many2one(
        comodel_name='prestashop.backend',
        string='PS Backend',
        required=True,
        ondelete='restrict'
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    prestashop_id = fields.Integer('ID on PrestaShop', copy=False)
    no_export = fields.Boolean('No export to PrestaShop', default=False)

    #     _sql_constraints = [
    #         ('prestashop_uniq', 'unique(backend_id, prestashop_id)',
    #          'A record with same ID on PrestaShop already exists.'),
    #     ]

    @api.constrains('backend_id', 'prestashop_id')
    def _check_prestashop_uniq(self):
        # as there is a chance that multiple bindings with prestashop_id 0, we removed te sql constraint
        res = dict()
        cr = self._cr
        query = 'SELECT "{}", "{}" FROM "{}" '.format(
            "backend_id",
            "prestashop_id",
            self._table,
        )
        cr.execute(query)
        for backend_id, prestashop_id in cr.fetchall():
            if not prestashop_id:
                continue
            if (backend_id, prestashop_id) not in res:
                res[(backend_id, prestashop_id)] = True
            else:
                raise ValidationError(
                    _(
                        "A record in {} with same Prestashop ID {} already exists".format(
                        self._name, prestashop_id)))

    def check_active(self, backend):
        if not backend.active:
            raise JobError(
                f"Backend {backend.name} is inactive please consider changing this"
                "The job will be retried later."
            )

    @api.model
    def import_record(self, backend, prestashop_id, force=False,
                      ps_read_data=False, **kwargs):
        """ Import a record from PrestaShop """
        self.check_active(backend)
        if force:
            raise ValidationError(_("import_recrd with force>> is it needed?trace it"))
        with backend.work_on(self._name) as work:
            importer = work.component(usage="prestashop.importer")
            return importer.run(prestashop_id, force=force, ps_read_data=ps_read_data,
                                **kwargs)

    @api.model
    def import_record_merge(self, backend, prestashop_id, imported_dependency=False, **kwargs):
        """ Import a record from PrestaShop with matching"""
        self.check_active(backend)
        if self._name in [
            "prestashop.product.image",  # TODO move to new module
            "prestashop.sale.order",
            "prestashop.sale.order.line",
        ]:
            importer_usage = "prestashop.importer"
        else:
            importer_usage = 'prestashop.match.importer'
        with backend.work_on(self._name) as work:
            importer = work.component(usage=importer_usage)
            return importer.run(prestashop_id, imported_dependency=imported_dependency, **kwargs)

    @api.model
    def import_batch(self, backend, filters=None, **kwargs):
        """ Prepare a batch import of records from PrestaShop """
        self.check_active(backend)
        if filters is None:
            filters = {}
        with backend.work_on(self._name) as work:
            importer = work.component(usage='prestashop.batch.importer')
            return importer.run(filters=filters, **kwargs)

    @api.model
    def import_batch_merge(self, backend, filters=None, **kwargs):
        """ Prepare a batch import of records from PrestaShop """
        self.check_active(backend)
        if filters is None:
            filters = {}
        with backend.work_on(self._name) as work:
            importer = work.component(usage='prestashop.batch.match.importer')
            return importer.run(filters=filters, **kwargs)

    def export_record(self, field_names=None):
        """ Export a record on PrestaShop """
        self.ensure_one()
        self.check_active(self.backend_id)
        if not self.backend_id.export_active:
            raise JobError(
                _("Update to PS Failed: Export is inactive for %s" % self.backend_id.name))
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='prestashop.exporter')
            return exporter.run(self, field_names)

    @api.model
    def export_batch(self, backend, filters=None, **kwargs):
        """ Prepare a batch export of records """
        self.check_active(backend)
        if not backend.export_active:
            raise JobError(
                _("Update to PS Failed: Export is inactive for %s" % backend.name))
        if self.no_export:
            raise JobError(
                _("Update to PS Failed: No Export to Prestashop active for binding %s" % self.display_name))
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='prestashop.batch.exporter')
            return exporter.run(filters=filters, **kwargs)

    # # DELETE
    # def delete_record(self):
    #     self.ensure_one()
    #     # For images, it is override
    #     self.with_delay().export_delete_record(self.backend_id, self.prestashop_id)
    #     return True

    def export_delete_record(self, backend, external_id, attributes=None):
        """ Delete a record on PrestaShop """
        self.check_active(backend)
        with backend.work_on(self._name) as work:
            deleter = work.component(usage='prestashop.deleter')
            return deleter.run(external_id, attributes=attributes)

    def resync(self):
        for record in self:
            func = record.import_record_merge
            if self.env.context.get("connector_delay"):
                func = record.with_delay(
                    description=f"Import ID {record.prestashop_id}",
                    identity_key=identity_exact
                ).import_record_merge
            func(record.backend_id, record.prestashop_id)
        return True

    def re_export(self):
        for record in self:
            func = record.export_record
            if self.env.context.get('connector_delay'):
                identity_key = record.backend_id.generate_identity_key(record)
                func = record.with_delay(
                    identity_key=identity_key,
                    description=f"Export ID {record.odoo_id.id}({record.odoo_id.display_name})",
                ).export_record
            func()
        return True


class PrestashopBindingOdoo(models.AbstractModel):
    _name = 'prestashop.binding.odoo'
    _inherit = 'prestashop.binding'
    _description = 'PrestaShop Binding with Odoo binding (abstract)'

    def _get_selection(self):
        records = self.env['ir.model'].search([])
        return [(r.model, r.name) for r in records] + [('', '')]

    # 'odoo_id': odoo-side id must be re-declared in concrete model
    # for having a many2one instead of a reference field
    odoo_id = fields.Reference(
        required=True,
        ondelete='cascade',
        string='Odoo binding',
        selection=_get_selection,
    )

    #     _sql_constraints = [
    #         ('prestashop_erp_uniq', 'unique(backend_id, odoo_id)',
    #          'An ERP record with same ID already exists on PrestaShop.'),
    #     ]

    @api.constrains('backend_id', 'odoo_id')
    def _check_odoo_uniq(self):
        res = {}

        model_has_multiple_binding = self.env["ir.config_parameter"].get_param(
            "ps.multi_bind.{}".format(self._name)
        )
        if model_has_multiple_binding:
            return
        cr = self._cr
        query = 'SELECT "{}", "{}" FROM "{}" '.format(
            "backend_id", "odoo_id", self._table
        )
        cr.execute(query)
        for backend_id, odoo_id in cr.fetchall():
            if not odoo_id:
                continue
            if (backend_id, odoo_id) not in res:
                res[(backend_id, odoo_id)] = 1
            else:
                raise ValidationError(
                    _(
                        "Multiple bindings for a record in {} with odoo ID {}".format(
                        self._name, odoo_id)))
