# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import base64
import logging

from odoo.addons.component.core import Component

from odoo import _, fields, models, exceptions
from odoo.tools import config
from ...components.backend_adapter import PrestaShopWebServiceImage
from prestapyt import PrestaShopWebServiceError


_logger = logging.getLogger(__name__)


class ProductImage(models.Model):
    _inherit = "base_multi_image.image"

    front_image = fields.Boolean()
    prestashop_bind_ids = fields.One2many(
        comodel_name="prestashop.product.image",
        inverse_name="odoo_id",
        string="PrestaShop Bindings",
    )
    # ps_product_tmpl_id = fields.Many2one('prestashop.product.template', 'Prestashop Product Template')

    def storage_to_filestore(self):
        for record in self:
            if record.storage == 'url':
                image_from_url = record._get_image_from_url()
                # filename = record.filename or record.url.split('/')[-1]
                # ir_attachment_dict = {
                #     'name': record.name,
                #     'type': 'binary',
                #     'datas': image_from_url,
                #     'datas_fname': record.filename or filename,
                #     'mimetype': 'image/jpeg'
                #     }
                # ir_attachment = self.env['ir.attachment'].create(ir_attachment_dict)
                # record.with_context(connector_no_export=True).write({
                #     'storage': 'filestore',
                #     # 'name': record.name,
                #     # 'extension': record.extension,
                #     'attachment_id': ir_attachment.id
                #     })
                record.with_context(connector_no_export=True).write({
                    'storage': 'filestore',
                    #                 'name': record.name,
                    #                 'extension': record.extension,
                    'attachment_image': image_from_url
                })
        return


class PrestashopProductImage(models.Model):
    _name = "prestashop.product.image"
    _inherit = "prestashop.binding"
    _inherits = {"base_multi_image.image": "odoo_id"}
    _description = "Product image prestashop bindings"

    odoo_id = fields.Many2one(
        comodel_name="base_multi_image.image",
        required=True,
        ondelete="cascade",
        string="Product image",
    )
    # In case the PS has multiple bindings for same product, it is necessary
    ps_product_tmpl_id = fields.Many2one('prestashop.product.template',
                                         'Prestashop Product Template')

    def import_product_image(self, backend, resource, product_tmpl_id, image_id,
                             **kwargs):
        """Import a product image"""
        with backend.work_on(self._name) as work:
            importer = work.component(usage='prestashop.importer')
            return importer.run(resource, product_tmpl_id, image_id)

    def delete_record(self):
        self.ensure_one()
        prestashop_dict = {}
        main_resource = self.owner_model == 'product.category' and 'categories' or 'products'
        if self.owner_model == 'product.category':
            prestashop_id = False
        else:
            prestashop_id = self.prestashop_id
        #         with self.backend_id.work_on('prestashop.%s'%self.owner_model) as work:
        main_binding_obj = self.env[self.owner_model].browse(self.owner_id).prestashop_bind_ids.filtered(
            lambda x: x.backend_id == self.backend_id)
        main_resource_id = main_binding_obj.prestashop_id
        #         _logger.info( "Deleting record:::main_binding_obj: %s,ps_id: %s, owner_id: %s"%(main_binding_obj,main_resource_id,self.env[self.owner_model].browse(self.owner_id)))
        if main_resource_id:
            #                 prestashop_dict.update({(
            #                              main_resource,
            #                              main_resource_id,
            #                              prestashop_id):True})

            #         res = super(ProductImage, self.with_context(connector_no_export=True)).unlink()
            resource_path = '/images/{}/{}'.format(
                main_resource, main_resource_id)
            if prestashop_id:
                resource_path = '%s/%s' % (resource_path, prestashop_id)

            return self.with_delay().export_delete_record(self.backend_id, prestashop_id, dict(resource=resource_path))


class ProductImageAdapter(Component):
    _name = "prestashop.product.image.adapter"
    _inherit = "prestashop.crud.adapter"
    _apply_on = "prestashop.product.image"
    _prestashop_image_model = "products"
    _prestashop_model = "/images"
    _export_node_name = "/images"
    _export_node_name_res = "image"

    # pylint: disable=method-required-super

    def search(self, resource, options=None):
        """Retrieve (GET) a resource and return a list of its ids.

        Is not supposed to be called with an id
        or whatever in the resource line 'addresses/1'
        But only with 'addresses' or 'products' etc...

        :param resource: string of the resource to search like,
            ie: 'addresses', 'products', 'manufacturers', etc.
        :param options: optional dict of parameters to filter the search
            (one or more of 'filter', 'display', 'sort', 'limit', 'schema')
        :return: list of ids as int
        """

        def dive(response, level=1):
            # not deterministic but we know that we only have one key
            # in the response for the first 2 levels like
            # {'addresses': {'address': ...} this method has just
            # purpose to dive of n level in the response
            if not response:
                return False
            if level > 0:
                return dive(response[list(response.keys())[0]], level=level - 1)
            return response

        # returned response looks like :
        # for many resources :
        # {'addresses': {'address': [{'attrs': {'id': '1'}, 'value': ''},
        #                            {'attrs': {'id': '2'}, 'value': ''},
        #                            {'attrs': {'id': '3'}, 'value': ''}]}}
        # for one resource :
        # {'addresses': {'address': {'attrs': {'id': '1'}, 'value': ''}}}
        # for zero resource :
        # {'addresses': ''}
        response = self.client.get(resource, options=options)

        elems = dive(response)
        # when there is only 1 resource, we do not have a list in the response
        if not elems:
            return []
        if isinstance(elems, dict):
            elems = elems.get('declination', [])
        if isinstance(elems, list):
            ids = [int(elem['attrs']['id']) for elem in elems]
        else:
            ids = [int(elems['attrs']['id'])]
        return ids

    # def connect(self):
    #     debug = False
    #     if config["log_level"] == "debug":
    #         debug = True
    #     return PrestaShopWebServiceImage(
    #         self.prestashop.api_url, self.prestashop.webservice_key, debug=debug
    #     )

    def read(self, resource, resource_id, image_id, options=None):
        api = PrestaShopWebServiceImage(self.prestashop.api_url,
                                        self.prestashop.webservice_key)
        res = api.get_image(
            resource,
            resource_id,
            image_id,
            options=options
        )
        return res

    def create(self, attributes=None):
        api = self.connect()
        # TODO: odoo logic in the adapter? :-(
        url = "{}/{}".format(self._prestashop_model, attributes["id_product"])
        return api.add(
            url,
            files=[
                (
                    "image",
                    attributes["filename"],
                    base64.b64decode(attributes["content"]),
                )
            ],
        )

    def create(self, attributes=None):
        api = PrestaShopWebServiceImage(
            self.prestashop.api_url, self.prestashop.webservice_key)
        # TODO: odoo logic in the adapter? :-(
        if 'id_category' in attributes:  # ?ps_method=PUT
            url = '/images/{}/{}'.format('categories', attributes['id_category'])
        else:
            url = '/images/{}/{}'.format('products', attributes['id_product'])
        a = attributes.copy()
        del a['content']
        _logger.debug(
            'method create, model %s, attributes %s',
            self._prestashop_model, a)
        if 'id_category' in attributes:
            # url_del = '{}/images/{}/{}'.format(
            #     api._api_url, 'categories', attributes['id_categories'])
            # try:
            # _logger.info("CREATE::: DELETE EXISTING IMAGES EXECUTED for %s" % (url_del) )

            # api._execute(url_del, 'DELETE')
            # except:
            #
            #     _logger.info(
            #         'method Delete failed!!!, url %s, attributes %s',
            #         url_del, str(a))
            #     pass
            try:
                # For categories no id is generated
                res = api.add(url, files=[(
                    'image',
                    attributes['filename'],
                    base64.b64decode(attributes['content']))
                ])
            except PrestaShopWebServiceError as Err:
                if 'PUT method' in "%s" % Err:
                    url = '/images/{}/{}/?ps_method=PUT'.format('categories', attributes['id_category'])
                    _logger.debug(
                        'method create with PUT, model %s, URL %s',
                        self._prestashop_model, url)

                    try:
                        res = api.add(url, files=[(
                            'image',
                            attributes['filename'],
                            base64.b64decode(attributes['content']))
                        ])
                    except:
                        pass

            # except:
            res = {'prestashop': {'image': {'id': "-%s" % attributes['id_category']}}}
        else:
            res = api.add(url, files=[(
                'image',
                attributes['filename'],  # .encode('utf-8')
                base64.b64decode(attributes['content'])
            )])

        if not self._export_node_name_res:
            raise exceptions.UserError(
                _("export_node_name_res not set for adapter %s" % self._prestashop_model))
        if self._export_node_name_res:
            _logger.debug("CREATE::: IMAGE ADD EXECUTED for %s with res %s" % (url, res['prestashop'][
                self._export_node_name_res]['id']))
            return res['prestashop'][self._export_node_name_res]['id']
        return res

    def write(self, id_, attributes=None):
        api = PrestaShopWebServiceImage(
            self.prestashop.api_url, self.prestashop.webservice_key)
        a = attributes.copy()
        del a['content']
        _logger.debug(
            'method write, model %s, attributes %s',
            self._prestashop_model, a)
        # TODO: odoo logic in the adapter? :-(
        if 'id_category' in attributes:
            url = '/images/{}/{}'.format('categories', attributes['id_category'])
            url_del = '{}/images/{}/{}'.format(
                api._api_url, 'categories', attributes['id_category'])
        else:
            url = '/images/{}/{}'.format('products', attributes['id_product'])
            url_del = '{}/images/{}/{}/{}'.format(
                api._api_url, 'products', attributes['id_product'], id)
            try:
                _logger.debug("WRITE::: IMAGE DELETE EXECUTED for %s" % url)
                api._execute(url_del, 'DELETE')
            except:
                _logger.debug(
                    'method Delete failed!!!, url %s, attributes %s',
                    url_del, str(a))
                pass
        if 'id_category' in attributes:
            try:
                # For categories no id is generated
                res = api.add(url, files=[(
                    'image',
                    attributes['filename'],
                    base64.b64decode(attributes['content']))
                ])
            except PrestaShopWebServiceError as Err:
                if 'PUT method' in "%s" % Err:
                    url = '/images/{}/{}/?ps_method=PUT'.format('categories', attributes['id_category'])
                    _logger.debug(
                        'method create with PUT, model %s, URL %s',
                        self._prestashop_model, url)
                    try:
                        res = api.add(url, files=[(
                            'image',
                            attributes['filename'],
                            base64.b64decode(attributes['content']))
                        ])
                    except:
                        pass

            res = {'prestashop': {'image': {'id': "-%s" % attributes['id_category']}}}
        else:
            res = api.add(url, files=[(
                'image',
                attributes['filename'],
                base64.b64decode(attributes['content'])
            )])
        if self._export_node_name_res:
            _logger.debug("WRITE::: IMAGE ADD EXECUTED for %s with res %s" % (url, res['prestashop'][
                self._export_node_name_res]['id']))
            return res['prestashop'][self._export_node_name_res]['id']
        return res

    def delete(self, resource, id=None, attributes=None):  # TODO
        """ Delete a image record on the external system """
        api = PrestaShopWebServiceImage(
            self.prestashop.api_url, self.prestashop.webservice_key)
        url_del = '{}/{}'.format(api._api_url, resource)
        url_del = url_del.replace('///', '/')
        _logger.debug("IMAGE DELETE EXECUTED for %s" % url_del)
        return api._execute(url_del, 'DELETE')
