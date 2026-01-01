# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class PrestashopBackend(models.Model):
    _inherit = 'prestashop.backend'

    import_manufacturers_since = fields.Datetime('Import Manufacturers since')

    def import_manufacturers(self):
        self.ensure_one()
        since_date = self.import_manufacturers_since
        self.env['prestashop.manufacturer'].with_delay(priority=10).import_manufacturers(
            self, since_date=since_date,
        )
        self.import_manufacturers_since = fields.datetime.now()
        return True

    @api.model
    def _scheduler_import_manufacturers(self, domain=None):
        self.search(domain or []).import_manufacturers()
