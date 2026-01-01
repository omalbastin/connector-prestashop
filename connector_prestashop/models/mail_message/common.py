# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields
from odoo.addons.component.core import Component


class MailMessage(models.Model):
    _inherit = 'mail.message'

    prestashop_bind_ids = fields.One2many(
        comodel_name='prestashop.mail.message',
        inverse_name='odoo_id',
        string='PrestaShop Bindings',
    )
    prestashop_bind_other_ids = fields.One2many(
        comodel_name='prestashop.mail.message.other',
        inverse_name='odoo_id',
        string='PrestaShop Bindings for other messages',
    )


class PrestashopMailMessage(models.Model):
    _name = "prestashop.mail.message"
    _inherit = "prestashop.binding.odoo"
    _inherits = {'mail.message': 'odoo_id'}
    _description = "Mail message prestashop bindings: messages"

    odoo_id = fields.Many2one(
        comodel_name='mail.message',
        required=True,
        ondelete='cascade',
        string='Message',
    )


class PrestashopMailMessageOther(models.Model):
    _name = "prestashop.mail.message.other"
    _inherit = "prestashop.binding.odoo"
    _inherits = {'mail.message': 'odoo_id'}
    _description = "prestashop other messages"

    odoo_id = fields.Many2one(
        comodel_name='mail.message',
        required=True,
        ondelete='cascade',
        string='Message',
    )


class MailMessageAdapter(Component):
    _name = 'prestashop.mail.message.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.mail.message'
    _prestashop_model = 'customer_messages'

    def read(self, id_, attributes=None):
        """ Merge message and thread datas

        :rtype: dict
        """
        api = self.client
        res = api.get(self._prestashop_model, id_, options=attributes)
        first_key = list(res.keys())[0]
        message_data = res[first_key]
        thread_data = api.get('customer_threads',
                              message_data['id_customer_thread'],
                              options=attributes)
        first_key = list(thread_data.keys())[0]
        del thread_data[first_key]['id']
        del thread_data[first_key]['date_add']
        message_data.update(thread_data[first_key])
        return message_data


#     @property
#     def _prestashop_model(self):
#         return self.backend_record.get_version_ps_key('customer_messages')

class MailMessageOtherAdapter(Component):
    _name = 'prestashop.mail.message.other.adapter'
    _inherit = 'prestashop.adapter'
    _apply_on = 'prestashop.mail.message.other'
    _prestashop_model = 'messages'


class MailMessageBinder(Component):
    _name = 'prestashop.mail.message.binder'
    _inherit = 'prestashop.binder'
    _apply_on = 'prestashop.mail.message'


class MailMessageOtherBinder(Component):
    _name = 'prestashop.mail.message.other.binder'
    _inherit = 'prestashop.binder'
    _apply_on = 'prestashop.mail.message.other'

