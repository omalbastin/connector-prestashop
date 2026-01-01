##############################################################################
#
#    ODOO, Open Source Management Solution
#    Copyright (C) 2016 O4 ODOO
#    For more details, check COPYRIGHT and LICENSE files
#
##############################################################################

from odoo import _, api, models, fields


class QueueJob(models.Model):
    _inherit = "queue.job"

    def related_action_record(self, binding_id_pos=0):
        self.ensure_one()
        print(self, self.args, self.kwargs,'ffffffffffffrelated_action_recordffffffffff')
        binding_model = self.model_name
        binding_id = self.args[binding_id_pos]
        record = self.env[binding_model].browse(binding_id)
        odoo_name = record.odoo_id._name

        action = {
            "name": _(odoo_name),
            "type": "ir.actions.act_window",
            "res_model": odoo_name,
            "view_type": "form",
            "view_mode": "form",
            "res_id": record.odoo_id.id,
        }
        return action