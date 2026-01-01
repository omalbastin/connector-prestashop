# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging

from odoo.addons.component.core import AbstractComponent
from odoo.addons.connector.exception import NetworkRetryableError
from prestapyt import PrestaShopWebServiceDict, PrestaShopWebServiceError
from requests.exceptions import (
    ConnectionError as ConnError,
)
from requests.exceptions import (
    HTTPError,
    RequestException,
    Timeout,
)

_logger = logging.getLogger(__name__)



class PrestaShopWebServiceImage(PrestaShopWebServiceDict):

    def get_image(self, resource, resource_id=None, image_id=None, options=None):
        resources_dict = dict(
            products="product",
            categories="category",
            manufacturers="manufacturer",
            suppliers="supplier",
        )
        full_url = self._api_url + "images/" + resource
        if resource_id is not None:
            full_url += f"/{resource_id}"
            if image_id is not None:
                full_url += "/%s" % (image_id)
        if options is not None:
            self._validate_query_options(options)
            full_url += f"?{self._options_to_querystring(options)}"
        response = self._execute(full_url, "GET")
        if response.content:
            image_content = base64.b64encode(response.content)
        else:
            image_content = ""

        record = {
            "type": response.headers["content-type"],
            "content": image_content,
            "id_" + resources_dict[resource]: resource_id,
            "id_image": image_id,
        }

        record["full_public_url"] = self.get_image_public_url(record)
        return record

    def get_image_public_url(self, record):
        extension = ""
        if record["type"] == "image/jpeg":
            extension = ".jpg"
        url = self._api_url.replace("/api", "")
        if "id_category" in record:
            url += "/c/%s-category_default" % record["id_category"]  # id-image_type
            url += "/{}{}".format(
                record["id_category"], extension
            )  # Any name possible!
            return url
        url += "/img/p/" + "/".join(list(record["id_image"]))

        url += "/" + record["id_image"] + extension
        return url

