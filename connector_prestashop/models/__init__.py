# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

# keep this at the top!
from . import binding

from . import prestashop_backend
from . import prestashop_shop_group
from . import res_lang
from . import res_country
from . import res_country_state
from . import res_currency
from . import res_partner
from . import res_partner_category
from . import product_category
from . import product_attribute
# from . import product_image
from . import product_pricelist
from . import product_template
from . import product_product
from . import product_supplierinfo
from . import product_tags
from . import account_move
# from . import account_payment_mode
from . import payment_method
from . import account_tax
from . import account_tax_group
from . import delivery_carrier
from . import mail_message
# from . import payment #TODO do we need this as payment_method is doing the same

from . import sale_order
from . import sale_order_state
from . import stock_move
from . import stock_tracking
from . import stock_warehouse
from . import queue_job
# from . import base
