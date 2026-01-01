# © 2016-Today Omal Bastin <omalbastin@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import threading
from contextlib import closing, contextmanager

from odoo.addons.queue_job.delay import group, chain
from odoo.addons.queue_job.exception import FailedJobError, RetryableJobError
from odoo.addons.queue_job.job import identity_exact

import odoo
from odoo import _
from odoo.addons.component.core import AbstractComponent

_logger = logging.getLogger(__name__)

RETRY_ON_ADVISORY_LOCK = 1  # seconds
RETRY_WHEN_CONCURRENT_DETECTED = 1  # seconds


class PrestashopImporter(AbstractComponent):
    """ Base importer for PrestaShop """

    _name = 'prestashop.importer'
    _inherit = ['base.importer', 'base.prestashop.connector']
    _usage = 'prestashop.importer'

    _base_mapper_usage = 'prestashop.import.mapper'

    def __init__(self, environment):
        """
        :param environment: current environment (backend, session, ...)
        :type environment: :py:class:`connector.connector.ConnectorEnvironment`
        """
        super().__init__(environment)
        self.prestashop_id = None
        self.prestashop_record = None
        self.ps_read_data = None

    def _get_prestashop_data(self):
        """Return the raw prestashop data for ``self.prestashop_id``"""
        if self.ps_read_data:
            return self.ps_read_data
        return self.backend_adapter.read(self.prestashop_id)

    def _split_per_language(self, record, fields=None):
        # Managed under traslatable importer
        split_record = {}
        split_record[self.backend_record.default_language] = record
        return split_record

    def _has_to_skip(self, binding=False):
        """Return True if the import can be skipped"""
        return False

    def _import_dependency(
            self, prestashop_id, binding_model,
            importer_usage=None, always=False,
            with_delay=False, **kwargs
    ):
        """Import a dependency.

        The importer class is a class or subclass of
        :class:`PrestashopImporter`. A specific class can be defined.

        :param prestashop_id: id of the related binding to import
        :param binding_model: name of the binding model for the relation
        :type binding_model: str | unicode
        :param importer_component: component to use for import
                                   By default: 'importer'
        :type importer_component: Component
        :param always: if True, the record is updated even if it already
                       exists, note that it is still skipped if it has
                       not been modified on Prestashop since the last
                       update. When False, it will import it only when
                       it does not yet exist.
        :type always: boolean
        """
        if not prestashop_id:
            return
        if not importer_usage:
            importer_usage = "prestashop.match.importer"
        binder = self.binder_for(binding_model)
        if always or not binder.to_internal(prestashop_id):
            if not with_delay:
                importer = self.component(usage=importer_usage, model_name=binding_model)
                # try:
                importer.run(prestashop_id, **kwargs)
                # except NothingToDoJob:
                #     _logger.info(
                #         'Dependency import of %s(%s) has been ignored.',
                #         binding_model._name, prestashop_id
                #     )
            else:
                return self.env[binding_model].with_delay(
                    description=f"Import {binding_model} with ID {prestashop_id}",
                    identity_key=identity_exact
                ).import_record_merge(self.backend_record, prestashop_id, **kwargs)

    def _import_dependencies(self):
        """Import the dependencies for the record"""
        return

    def _map_data(self):
        """ Returns an instance of
        :py:class:`~odoo.addons.connector.unit.mapper.MapRecord`

        """
        return self.mapper.map_record(self.prestashop_record)

    def _validate_data(self, data):
        """ Check if the values to import are correct

        Pro-actively check before the ``Model.create`` or
        ``Model.update`` if some fields are missing

        Raise `InvalidDataError`
        """
        return

    def _get_binding(self):
        """Return the odoo id from the prestashop id"""
        return self.binder.to_internal(self.prestashop_id)

    def _update_context(self, **kwargs):
        return dict(connector_no_export=True,
                    **kwargs)

    def _create_context(self):
        return dict(connector_no_export=True,
                    )

    def _create_data(self, map_record):
        return map_record.values(for_create=True)

    def _update_data(self, map_record):
        return map_record.values()

    def _create(self, data):
        """Create the odoo record"""
        # special check on data before import
        self._validate_data(data)
        binding = self.model.with_context(**self._create_context()).create(data)
        _logger.debug(
            '%d created from prestashop %s', binding, self.prestashop_id)
        return binding

    def _update(self, binding, data):
        """Update an odoo record"""
        # special check on data before import
        self._validate_data(data)
        binding.with_context(**self._update_context()).write(data)
        _logger.debug(
            '%d updated from prestashop %s', binding, self.prestashop_id)
        return

    def _before_import(self, binding=None):
        """ Hook called before the import, when we have the PrestaShop
        data"""
        return

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        return

    @contextmanager
    def do_in_new_connector_env(self, model_name=None):
        """ Context manager that yields a new connector environment

        Using a new Odoo Environment thus a new PG transaction.

        This can be used to make a preemptive check in a new transaction,
        for instance to see if another transaction already made the work.
        """
        registry = odoo.modules.registry.Registry(self.env.cr.dbname)
        with closing(registry.cursor()) as cr:
            try:
                new_env = odoo.api.Environment(cr, self.env.uid, self.env.context)
                # connector_env = self.connector_env.create_environment(
                #     self.backend_record.with_env(new_env),
                #     model_name or self.model._name,
                #     connector_env=self.connector_env
                # )
                with self.backend_record.with_env(new_env).work_on(
                        self.model._name
                ) as work2:
                    yield work2
            except BaseException:
                cr.rollback()
                raise
            else:
                # Despite what pylint says, this a perfectly valid
                # commit (in a new cursor). Disable the warning.
                self.env.flush_all()  # TODO FIXME check if and why flush is mandatory here
                if not getattr(threading.current_thread(), "testing", False):
                    cr.commit()  # pylint: disable=invalid-commit

    def _check_in_new_connector_env(self):
        # with self.do_in_new_connector_env() as new_connector_env:
        with self.do_in_new_connector_env():
            # Even when we use an advisory lock, we may have
            # concurrent issues.
            # Explanation:
            # We import Partner A and B, both of them import a
            # partner category X.
            #
            # The squares represent the duration of the advisory
            # lock, the transactions starts and ends on the
            # beginnings and endings of the 'Import Partner'
            # blocks.
            # T1 and T2 are the transactions.
            #
            # ---Time--->
            # > T1 /------------------------\
            # > T1 | Import Partner A       |
            # > T1 \------------------------/
            # > T1        /-----------------\
            # > T1        | Imp. Category X |
            # > T1        \-----------------/
            #                     > T2 /------------------------\
            #                     > T2 | Import Partner B       |
            #                     > T2 \------------------------/
            #                     > T2        /-----------------\
            #                     > T2        | Imp. Category X |
            #                     > T2        \-----------------/
            #
            # As you can see, the locks for Category X do not
            # overlap, and the transaction T2 starts before the
            # commit of T1. So no lock prevents T2 to import the
            # category X and T2 does not see that T1 already
            # imported it.
            #
            # The workaround is to open a new DB transaction at the
            # beginning of each import (e.g. at the beginning of
            # "Imp. Category X") and to check if the record has been
            # imported meanwhile. If it has been imported, we raise
            # a Retryable error so T2 is rollbacked and retried
            # later (and the new T3 will be aware of the category X
            # from the its inception).
            binder = self.binder_for(model=self.model._name)
            # binder = new_connector_env.get_connector_unit(Binder)
            if binder.to_internal(self.prestashop_id):
                raise RetryableJobError(
                    'Concurrent error. The job will be retried later',
                    seconds=RETRY_WHEN_CONCURRENT_DETECTED,
                    ignore_retry=True
                )

    def force_update_if_needed(self, **kwargs):
        for key in kwargs:
            if key.startswith("force_update"):
                ps_field = key.replace("force_update_", "")
                self.prestashop_record.update({ps_field: kwargs[key]})

    def run(
            self, prestashop_id, imported_dependency=False,
            import_dependencies_only=False, ps_read_data=False,
            **kwargs
    ):
        """Run the synchronization
        import_dependencies_only and imported_dependency are for managing importing
        :param prestashop_id: identifier of the record on PrestaShop
        """
        _logger.debug("Inside PrestashopImporter %s run, %s,imported_dependency=%s, import_dependencies_only=%s, %s" % (
            self._name, self, imported_dependency, import_dependencies_only, kwargs))
        self.prestashop_id = prestashop_id
        self.ps_read_data = ps_read_data
        lock_name = "import({}, {}, {}, {})".format(
            self.backend_record._name,
            self.backend_record.id,
            self.model._name,
            self.prestashop_id,
        )
        # Keep a lock on this import until the transaction is committed
        self.advisory_lock_or_retry(lock_name, retry_seconds=RETRY_ON_ADVISORY_LOCK)
        if not self.prestashop_record:
            self.prestashop_record = self._get_prestashop_data()

        self.force_update_if_needed(**kwargs)
        # put back a not active test domain so the rest of the import process
        # happen in normal conditions
        binding = self._get_binding().with_context(active_test=True)
        if not binding:
            self._check_in_new_connector_env()

        skip = self._has_to_skip(binding=binding)
        if skip:
            # TODO a notification that import is skipped
            return skip

        # import the missing linked resources
        if not imported_dependency:
            self._import_dependencies()
        if import_dependencies_only:  # TODO Check loop is happening or not
            return self.model.import_record_merge(self.backend_record,
                                                  self.prestashop_id,
                                                  imported_dependency=True)
        result = self._import(binding, **kwargs)
        return result

    def _import(self, binding, **kwargs):
        """ Import the external record.

        Can be inherited to modify for instance the session
        (change current user, values in context, ...)

        """

        map_record = self._map_data()
        self._before_import(binding)
        if binding:
            record = self._update_data(map_record)
        else:
            record = self._create_data(map_record)

        # special check on data before import
        self._validate_data(record)

        if binding:
            self._update(binding, record)
        else:
            binding = self._create(record)

        self.binder.bind(self.prestashop_id, binding)

        self._after_import(binding)
        odoo_rec_id = hasattr(binding, 'odoo_id') and binding.odoo_id.id or binding
        message = _('Record Imported with Odoo ID %s.')
        return message % odoo_rec_id


class BatchImporter(AbstractComponent):
    """ The role of a BatchImporter is to search for a list of
    items to import, then it can either import them directly or delay
    the import of each item separately.
    """
    _name = 'prestashop.batch.importer'
    _inherit = ['base.importer', 'base.prestashop.connector']
    _usage = 'prestashop.batch.importer'

    _page_size = 500
    _use_job_queue = True  # True for delayed import and False for direct import

    def run(self, filters=None, **kwargs):
        """ Run the synchronization
        This will split the batch and then import each records"""
        if filters is None:
            filters = dict()
        _logger.debug("Inside %s run, %s, %s" % (self._name, self, kwargs))
        chain_items = []
        if "limit" in filters:
            group_res = self._run_page(filters, **kwargs)
            if self._use_job_queue:
                chain_items.append(group_res)

        else:
            page_number = 0
            offset = page_number * self._page_size
            all_records = self.backend_adapter.search(filters)
            total_records = len(all_records)

            while total_records >= 1:
                filters["limit"] = "%d,%d" % (offset, self._page_size)
                group_res = self._run_page_splitter(filters, **kwargs)
                if self._use_job_queue:
                    chain_items.append(group_res)
                total_records -= self._page_size
                page_number += 1
                offset = page_number * self._page_size

        if chain_items:
            chain(*chain_items).delay()
        return True

    def _run_page_splitter(self, filters, **kwargs):
        model_obj = self.model
        if self._use_job_queue:
            model_obj = self.model.delayable(
                priority=10,
                description=f"Prepare Batch import {self.model._name} with filters {filters}",
                identity_key=identity_exact
            )
        return model_obj.import_batch(self.backend_record, filters, **kwargs)

    def _run_page(self, filters, **kwargs):
        record_ids = self.backend_adapter.search(filters)
        group_items = []
        for record_id in record_ids:
            res = self._import_record(record_id, **kwargs)
            if self._use_job_queue and res:
                group_items.append(res)

        if group_items:
            return group(*group_items)
        return True

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
                description=f"Import {self.model._name} with ID {record_id}",
                channel=channel,
                identity_key=identity_key
            )

        return model_obj.import_record(self.backend_record, record_id, **kwargs)


class TranslatableRecordImporter(AbstractComponent):
    """ Import one translatable record """
    _name = 'prestashop.translatable.importer'
    _inherit = 'prestashop.importer'
    #     _usage = 'prestashop.translatable.importer'

    _model_name = []

    _translatable_fields = []  # prestashop field names

    #     _default_language = 'en_US'#taking from prestashop backend

    def __init__(self, environment):
        """
        :param environment: current environment (backend, session, ...)
        :type environment: :py:class:`connector.connector.ConnectorEnvironment`
        """
        super().__init__(environment)
        self.main_lang_data = None
        self.main_lang = None
        self.other_langs_data = None

    def _get_odoo_language(self, prestashop_id):
        language_binder = self.binder_for('prestashop.res.lang')
        erp_language = language_binder.to_internal(prestashop_id)
        return erp_language

    def find_each_language(self, record):
        languages = {}
        for field in self._translatable_fields:
            # TODO FIXME in prestapyt
            if not isinstance(record[field]['language'], list):
                record[field]['language'] = [record[field]['language']]
            for language in record[field]['language']:
                if not language or language['attrs']['id'] in languages:
                    continue
                erp_lang = self._get_odoo_language(language['attrs']['id'])
                if erp_lang:
                    languages[language['attrs']['id']] = erp_lang.code
        return languages

    def _split_per_language(self, record, fields=None):
        """Split record values by language.

        @param record: a record from PS
        @param fields: fields whitelist
        @return a dictionary with the following structure:

            'en_US': {
                'field1': value_en,
                'field2': value_en,
            },
            'it_IT': {
                'field1': value_it,
                'field2': value_it,
            }
        """
        split_record = {}
        languages = self.find_each_language(record)

        if not languages:
            # TranslatableImporter can be used for any import.
            if self._translatable_fields:
                raise FailedJobError(
                    _('No language mapping defined. '
                      'Run "Synchronize base data".')
                )
            else:
                split_record[self.backend_record.default_language] = record
                return split_record
        for _language_id, language_code in languages.items():
            split_record[language_code] = record.copy()
        _fields = self._translatable_fields
        if fields:
            _fields = [x for x in _fields if x in fields]
        for field in _fields:
            for language in record[field]['language']:
                current_id = language['attrs']['id']
                code = languages.get(current_id)
                if not code:
                    # TODO: be nicer here.
                    # Currently if you have a language in PS
                    # that is not present in odoo
                    # the basic metadata sync is broken.
                    # We should present skip the language
                    # and maybe show a message to users.
                    raise FailedJobError(
                        _('No language could be found for the Prestashop lang '
                          'with id "%s". Run "Synchronize base data" again.') %
                        (current_id,)
                    )
                split_record[code][field] = language['value']
        return split_record

    def _update_context(self, **kwargs):
        context = super()._update_context(**kwargs)
        context['lang'] = None
        if self.main_lang:
            context['lang'] = self.main_lang
            context['no_external_translation'] = True
        # if self.main_lang == self.backend_record.company_id.lang:
        # context['lang'] = None
        # context['no_external_translation'] = True
        return context

    def _create_context(self):
        context = super()._create_context()
        context['lang'] = None
        if self.main_lang:
            context['lang'] = self.main_lang
            context['no_external_translation'] = True
        # if self.main_lang == self.backend_record.company_id.lang:
        # context['lang'] = None
        # context['no_external_translation'] = True
        return context

    def _map_data(self):
        """ Returns an instance of
        :py:class:`~odoo.addons.connector.unit.mapper.MapRecord`

        """
        return self.mapper.map_record(self.main_lang_data)

    def _import(self, binding, **kwargs):
        """ Import the external record.

        Can be inherited to modify for instance the session
        (change current user, values in context, ...)

        """
        # split prestashop data for every lang
        default_language = self.backend_record.default_language
        split_record = self._split_per_language(self.prestashop_record)
        if default_language in split_record:
            self.main_lang_data = split_record[default_language]
            self.main_lang = default_language
            del split_record[default_language]
        else:
            self.main_lang, self.main_lang_data = split_record.popitem()

        self.other_langs_data = split_record

        return super()._import(binding)

    # def _clean_html_translations(self, binding, fields_to_clean):
    #     IrTranslation = self.env['ir.translation']
    #     for field_name in fields_to_clean:
    #         IrTranslation.search([
    #             ('name', '=', f"{binding._name},{field_name}"),
    #             ('res_id', '=', binding.id),
    #         ]).unlink()
    #
    # def _before_import(self, binding=None):
    #     """ Hook called before the import, when we have the PrestaShop
    #     data"""
    #     if binding:
    #         html_translatable_fields = {
    #             field_name
    #             for field_name, field in binding._fields.items()
    #             if getattr(field, 'translate', False) and field.type == 'html'
    #         }
    #         self._clean_html_translations(binding, html_translatable_fields)
    #
    #     return
    #
    # #
    # # def _after_import(self, binding):
    # #     """Hook called at the end of the import"""
    # #     for lang_code, lang_record in self.other_langs_data.items():
    # #         map_record = self.mapper.map_record(lang_record)
    # #         binding.with_context(
    # #             lang=lang_code,
    # #             connector_no_export=True,
    # #             # no_external_translation=True
    # #         ).write(map_record.values())
    #
    # def _after_import(self, binding):
    #     """ Hook called at the end of the import, handling translations """
    #     IrTranslation = self.env['ir.translation'].sudo()
    #
    #     normal_fields = {
    #         name for name, field in binding._fields.items()
    #         if getattr(field, 'translate', False) and field.type != 'html'
    #     }
    #     html_fields = {
    #         name for name, field in binding._fields.items()
    #         if getattr(field, 'translate', False) and field.type == 'html'
    #     }
    #     # Gather all language data
    #     all_lang_datas = {self.main_lang: self.main_lang_data, **self.other_langs_data}
    #
    #     # Ensure canonical (lang=None) values exist first
    #     main_mapped = self.mapper.map_record(self.main_lang_data).values()
    #     main_html_vals = {k: v for k, v in main_mapped.items() if k in html_fields}
    #     if main_html_vals:
    #         binding.with_context(
    #             # lang=None,
    #             connector_no_export=True,
    #             # no_external_translation=True
    #         ).write(main_html_vals)
    #
    #     # Now handle translations properly
    #     for lang_code, lang_record in all_lang_datas.items():
    #         # if lang_code == self.main_lang:
    #         #     continue
    #         mapped = self.mapper.map_record(lang_record).values()
    #         normal_vals = {k: v for k, v in mapped.items() if k in normal_fields}
    #         if normal_vals:
    #             binding.with_context(
    #                 lang=lang_code,
    #                 connector_no_export=True,
    #                 no_external_translation=True
    #             ).write(normal_vals)
    #         # for field_name in html_fields:
    #         #     if field_name not in mapped:
    #         #         continue
    #         #
    #         #     field = binding._fields[field_name]
    #         #     src_terms = field.get_trans_terms(binding[field_name] or '')
    #         #
    #         #     # map_record value for this lang
    #         #     val_html = mapped[field_name] or ''
    #         #     trans_terms = field.get_trans_terms(val_html)
    #         #     for src_text, tgt_text in zip(src_terms, trans_terms):
    #         #         if not src_text:
    #         #             continue
    #         #         IrTranslation.sudo().create([{
    #         #             'lang': lang_code,
    #         #             'type': "model_terms",
    #         #             'name': f"{binding._name},{field_name}",
    #         #             'res_id': binding.id,
    #         #             'value': tgt_text,
    #         #             'src': src_text,
    #         #             'state': 'translated',
    #         #         }])
    #

    def _after_import(self, binding):
        """ Hook called at the end of the import """
        translatable_fields = {
            field_name
            for field_name, field in binding._fields.items()
            if getattr(field, 'translate', False)
        }
        map_record = self.mapper.map_record(self.main_lang_data)
        translated_values = {
            k: v for k, v in map_record.values().items() if k in translatable_fields
        }
        binding.with_context(
            lang=self.main_lang,
            connector_no_export=True,
            no_external_translation=True  # no extranal api for translation will work
        ).write(translated_values)
        #
        # lang_binding = binding.with_context(
        #     lang=self.main_lang,
        #     connector_no_export=True,
        #     no_external_translation=True #no extranal api for translation will work
        # )
        # for k, v in map_record.values().items():
        #     if k in translatable_fields:
        #         setattr(lang_binding, k, v)

        for lang_code, lang_record in self.other_langs_data.items():
            lang_map_record = self.mapper.map_record(lang_record)
            translated_values = {
                k: v for k, v in lang_map_record.values().items() if k in translatable_fields
            }
            binding.with_context(
                lang=lang_code,
                connector_no_export=True,
                no_external_translation=True #no extranal api for translation will work
            ).write(translated_values)
