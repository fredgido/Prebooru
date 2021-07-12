# APP/DATABASE/ARTIST_DB.PY

import datetime

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
    update_results = []
    update_columns = set(updatelist).intersection(COLUMN_ATTRIBUTES)
    UpdateColumnAttributes(illust_url, update_columns, updateparams)
