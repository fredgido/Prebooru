# APP/DATABASE/ILLUST_URL_DB.PY

# ##LOCAL IMPORTS
from .. import models, SESSION
from .base_db import UpdateColumnAttributes


# ##GLOBAL VARIABLES


COLUMN_ATTRIBUTES = ['illust_id', 'site_id', 'url', 'width', 'height', 'order', 'active']


# ## FUNCTIONS


def CreateIllustUrlFromParameters(createparams):
    illust_url = models.IllustUrl(**createparams)
    SESSION.add(illust_url)
    SESSION.commit()
    return illust_url


def UpdateIllustUrlFromParameters(illust_url, updateparams, updatelist):
    update_columns = set(updatelist).intersection(COLUMN_ATTRIBUTES)
    return UpdateColumnAttributes(illust_url, update_columns, updateparams)
