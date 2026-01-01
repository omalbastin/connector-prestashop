# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


# import logging
# _logger = logging.getLogger(__name__)


class ProductTagsImportMapper(Component):
    _apply_on = "prestashop.product.tag"
    _name = "prestashop.product.tag.import.mapper"
    _inherit = "prestashop.import.mapper"

    direct = [
        ('name', 'name'),
    ]

    @mapping
    def lang_id(self, record):
        ps_lang_id = record.get("id_lang")
        if not ps_lang_id:
            lang = self.env["res.lang"].search(
                [("code", "=", self.backend_record.default_language)]
            )
            binder = self.binder_for("prestashop.res.lang")
            ps_lang_id = binder.to_external(lang, True)
        return {"ps_lang_id": ps_lang_id}


class ProductTagsImporter(Component):
    """ Import the PrestaShop Product Tags. """

    _name = "prestashop.product.tag.importer"
    _inherit = "prestashop.translatable.importer"
    _apply_on = "prestashop.product.tag"

    _translatable_fields = [
        "name",
    ]

    # def _create_context(self):
    #     return {'connector_no_export': True, 'default_odoo_id': False}


class ProductTagsMergeImporter(Component):
    _name = "prestashop.product.tag.match.importer"
    _inherit = "prestashop.match.importer"
    _apply_on = "prestashop.product.tag"


class ProductTagsbatchMergeImporter(Component):
    _name = "prestashop.product.tag.batch.match.importer"
    _inherit = "prestashop.batch.match.importer"
    _apply_on = "prestashop.product.tag"
