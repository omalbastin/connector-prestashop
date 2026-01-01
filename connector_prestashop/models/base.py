##############################################################################
#
#    ODOO, Open Source Management Solution
#    Copyright © 2016-TODAY O4 ODOO
#    For more details, check COPYRIGHT and LICENSE files
#
##############################################################################

from collections import defaultdict

from odoo import models


class Base(models.AbstractModel):
    _inherit = 'base'

    #
    #     def unlink(self):
    #         if self._context.get('connector_no_export',False):
    #             return super(Base, self).unlink()
    #         #As on_record_unlink will not be able to get the bind_ids, I had to modify unlink
    #         backend_prestashop_dict = {}
    #         bindings = []
    #         for rec in self:
    #             if rec._name.startswith('prestashop'):
    #                 if hasattr(rec, 'backend_id'):
    #                     bindings.append(rec)
    #                 continue
    #             if not hasattr(rec, 'prestashop_bind_ids') or not rec.prestashop_bind_ids:
    #                 continue
    #             for binding in rec.prestashop_bind_ids:
    #                 bindings.append(binding)
    #         for binding in bindings:
    #             conn_env = binding.backend_id.get_environment(binding._name)
    #             binder = conn_env.get_connector_unit(Binder)
    #             adapter = conn_env.get_connector_unit(GenericAdapter)
    #             prestashop_id = binder.to_external(binding)
    #             if prestashop_id:
    #                 backend_prestashop_dict.update({(binding.backend_id.id,adapter._prestashop_model, prestashop_id):True})
    #
    #         res = super(Base, self).unlink()
    #         for  backend_id, psmodel, prestashop_id in backend_prestashop_dict:
    #             resource_path = '%s/%s' % (psmodel, prestashop_id)
    #             self.env['prestashop.backend'].browse(backend_id).with_delay(
    #                 ).export_delete_record(prestashop_id, resource_path)
    #         return res

    def correct_translations(self):
        """
        For a field with translation, found many translations for same lang and same record
        """
        self.ensure_one()
        if '__correct_translations_seen' not in self._context:
            self = self.with_context(__correct_translations_seen=defaultdict(set))

        seen_map = self._context['__correct_translations_seen']
        if self.id in seen_map[self._name]:
            return
        seen_map[self._name].add(self.id)
        lang_codes = self.env['res.lang'].search([]).mapped('code')

        def get_trans(field, rec):
            """ Return the 'name' of the translations to search for, together
                with the record ids corresponding to ``old`` and ``new``.
            """
            if field.inherited:
                pname = field.related[0]
                return get_trans(field.related_field, rec[pname])
            return "%s,%s" % (field.model_name, field.name), rec.id

        Translation = self.env['ir.translation']
        for name, field in self._fields.items():
            if field.type == 'one2many':
                # we must recursively copy the translations for o2m; here we
                # rely on the order of the ids to match the translations as
                # foreseen in copy_data()
                lines = self[name].sorted(key='id')
                for line in lines:
                    line.correct_translations()

            elif field.translate:
                # for translatable fields we copy their translations
                trans_name, source_id = get_trans(field, self)

                for code in lang_codes:
                    domain = [('name', '=', trans_name), ('res_id', '=', source_id)]
                    domain.append(('lang', '=', code))
                    first = False
                    all_trans = Translation.search(domain, order='id')
                    if all_trans:
                        first = all_trans[0]
                        unlink_trans = all_trans - first
                        unlink_trans.unlink()
