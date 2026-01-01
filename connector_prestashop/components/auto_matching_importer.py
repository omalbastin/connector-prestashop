# © 2016-Today Omal Bastin <omalbastin@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.addons.component.core import AbstractComponent
from odoo.addons.queue_job.delay import group, chain
from odoo.addons.queue_job.exception import FailedJobError
from odoo.addons.queue_job.job import identity_exact

from odoo import _

_logger = logging.getLogger(__name__)


class PrestashopMatchImporter(AbstractComponent):
    _name = "prestashop.match.importer"
    _inherit = ["base.importer", "base.prestashop.connector"]
    _usage = "prestashop.match.importer"

    _erp_field = None
    _ps_field = None

    # _copy_fields : a list of tuple with first element as the ps field and second as
    # erp field for direct copy
    _copy_fields = []
    # _create_match_bind_only: if true, binding created only for match.
    # used for mapping country, currency etc.
    _create_match_bind_only = False
    # _update_ps_id: in some cases, any change in data of a record in PS result in new
    # record and old record will also exist. if prestashop have multiple records for
    # same data, then update binding will update new prestashop id to the
    # existing other than creating. Used in features and its values, nutrition etc
    _update_ps_id = False
    # _update_with_ps_values: # make it false if you don't want to update the binding
    # with latest values from  ps in every pull
    _update_with_ps_values = True

    # _no_matching_needed: old name- _no_merging_needed. if set to true, will not check for any matches, a direct
    # import will be done.
    _no_matching_needed = False
    # _imported_dependency: sometimes we need to import the dependencies first (from
    # prestashop importer) so that we can make use of domain filter
    # (_odoo_domain_to_consider)to ease the matching of records. so once the
    # dependencies are imported we use _imported_dependency to flag that no need to
    # import dependencies again
    _imported_dependency = False
    _raise_nobinding_error = False
    _consider_inactive_records = True #whether we want to consider inactive odoo records for mapping

    #     _default_fields = []#same like direct keyword

    def _odoo_domain_to_consider(self, ps_dict):
        """Matching with all the records will be time consuming.
        so we use this method to define a domain and filter out the records"""
        return []

    def _odoo_fields_to_consider(self):
        """For comparing and matching data, we dont need all the erp record data to be read.
        so we use this method to specify the fields that we need in the compare_function"""
        fields_to_read = []
        if self._erp_field:
            fields_to_read.append(self._erp_field)
        for field in self._copy_fields:
            fields_to_read.append(field[1])
        if not fields_to_read:
            fields_to_read.append("id")
        return fields_to_read

    #     def _ps_fields_to_consider(self):
    #         return [self._ps_field]

    def compare_function(self, ps_val, erp_val, ps_dict, erp_dict):
        return False

    def run(self, record_id, imported_dependency=False, raise_nobinding_error=None, **kwargs):
        """Run the synchronization"""
        self._imported_dependency = imported_dependency
        self._raise_nobinding_error = raise_nobinding_error
        if self._no_matching_needed:
            binder = self.binder_for()
            binding = binder.to_internal(record_id)
            if not binding.id or self._update_with_ps_values:
                return self.model.import_record(
                    self.backend_record, record_id, **kwargs
                )
            return
        self._import_record(record_id, **kwargs)

    def _import_record(self, ps_record_id, with_delay=False, **kwargs):
        _logger.info("Inside _import_record %s run, %s, %s, " % (self._name, self, kwargs))
        erp_model_name = self.model.odoo_id._name  # next(iter(self.model._inherits))
        #         erp_rec_name = self.env[erp_model_name]._rec_name
        default_language = self.backend_record.default_language or "en_US"
        model = self.env[erp_model_name].with_context(
            active_test=not self._consider_inactive_records, lang=default_language, prefetch_fields=False
        )
        binding_model = self.model
        if with_delay:
            binding_model = self.model.with_delay(
                description=f"Import {self.model._name} with ID {ps_record_id}",
                identity_key=identity_exact,
            )
        binder = self.binder_for()
        # Check if the PS ID is already mapped to an OE ID
        binding = binder.to_internal(ps_record_id)
        ps_dict = False
        if not binding.id:
            adapter = self.backend_adapter
            ps_dict = adapter.read(ps_record_id, **kwargs)

            ps_translate_unit = self.component(usage="prestashop.importer")
            ps_dict_translated = ps_translate_unit._split_per_language(ps_dict)[default_language]
            # Loop on OE IDs
            odoo_domain_to_consider = self._odoo_domain_to_consider(ps_dict_translated)
            if odoo_domain_to_consider and not self._imported_dependency:
                return binding_model.import_record(
                    self.backend_record,
                    ps_record_id,
                    imported_dependency=False,
                    import_dependencies_only=True,
                    **kwargs
                )

            erp_ids = model.search(odoo_domain_to_consider)
            erp_list_dict = erp_ids.read(self._odoo_fields_to_consider())

            for erp_dict in erp_list_dict:
                # Search for a match
                erp_val = self._erp_field and erp_dict[self._erp_field] or False
                ps_val = self._ps_field and ps_dict_translated[self._ps_field] or False
                if self.compare_function(ps_val, erp_val, ps_dict_translated, erp_dict):
                    data = {
                        "odoo_id": erp_dict["id"],
                        "backend_id": self.backend_record.id,
                    }
                    for oe_field, ps_field in self._copy_fields:
                        data[oe_field] = erp_dict[ps_field]

                    binding_domain = [
                        ("odoo_id", "=", data["odoo_id"]),
                        ("prestashop_id", "=", 0),
                        ("backend_id", "=", data["backend_id"]),
                    ]
                    if self._update_ps_id:
                        binding_domain = [
                            ("odoo_id", "=", data["odoo_id"]),
                            ("backend_id", "=", data["backend_id"]),
                        ]
                    binding = self.model.search(binding_domain, limit=1)
                    if not binding:
                        binding = self.model.with_context(
                            connector_no_export=True
                        ).create(data)
                    binder.bind(ps_record_id, binding)
                    # mapping_found = True
                    break
        if not binding.id:
            if not self._create_match_bind_only:
                return binding_model.import_record(
                    self.backend_record,
                    ps_record_id,
                    imported_dependency=self._imported_dependency,
                    ps_read_data=ps_dict,
                    **kwargs
                )
            else:
                message = _(f"Matching record not found in model {erp_model_name} for "
                            f"ps ID {ps_record_id}. So cancelled")
                if self._raise_nobinding_error:
                    raise FailedJobError(message)
                return message
        elif self._update_with_ps_values:
            # Reimporting the record to update it with all correct values.
            return binding_model.import_record(
                self.backend_record,
                ps_record_id,
                imported_dependency=self._imported_dependency,
                ps_read_data=ps_dict,
                **kwargs
            )
        return True


class PrestashopMatchBatchImporter(AbstractComponent):
    _name = "prestashop.batch.match.importer"
    _inherit = ["base.importer", "base.prestashop.connector"]
    _usage = "prestashop.batch.match.importer"

    _page_size = 1000
    _use_job_queue = True  # True for delayed import and False for direct import

    def run(self, filters=None, **kwargs):
        """Run the synchronization"""

        if not filters:
            filters = {}
        chain_items = []
        if "limit" in filters:
            group_res = self._run_page(filters, **kwargs)
            if self._use_job_queue and group_res:
                chain_items.append(group_res)
        else:
            page_number = 0
            offset = page_number * self._page_size
            all_records = self.backend_adapter.search(filters)
            total_records = len(all_records)
            while total_records >= 1:
                filters["limit"] = "%d,%d" % (offset, self._page_size)
                group_res = self._run_page_splitter(filters, **kwargs)
                if self._use_job_queue and group_res:
                    chain_items.append(group_res)
                total_records -= self._page_size
                page_number += 1
                offset = page_number * self._page_size
        if chain_items:
            print(chain_items,"chain_itemschain_items")
            chain(*chain_items).delay()
        return True

    def _run_page_splitter(self, filters, **kwargs):
        model_obj = self.model
        if not self._use_job_queue:
            return model_obj.import_batch_merge(self.backend_record, filters, **kwargs)
        model_obj = self.model.delayable(
            priority=10,
            description=f"Prepare Batch match import {self.model._name} with filters {filters}",
            identity_key=identity_exact
        )
        return model_obj.import_batch_merge(self.backend_record, filters, **kwargs)

    def _run_page(self, filters, **kwargs):
        record_ids = self.backend_adapter.search(filters)
        group_items = []
        for record_id in record_ids:
            res = self._import_record(record_id, **kwargs)
            if self._use_job_queue and res:
                group_items.append(res)
        if group_items:
            return group(*group_items)
        return 

    def _import_record(self, record_id, **kwargs):
        """Import the record"""
        model_obj = self.model
        if self._use_job_queue:
            priority = kwargs.pop("priority", None)
            eta = kwargs.pop("eta", None)
            max_retries = kwargs.pop("max_retries", None)
            channel = kwargs.pop("channel", 'root.prestashop_import')
            identity_key = kwargs.pop("identity_key", identity_exact)
            model_obj = self.model.delayable(
                priority=priority,
                eta=eta,
                max_retries=max_retries,
                description=f"Match Import {self.model._name} with ID {record_id}",
                channel=channel,
                identity_key=identity_key,
            )

        return model_obj.import_record_merge(self.backend_record, record_id, **kwargs)
