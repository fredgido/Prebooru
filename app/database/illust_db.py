# APP/DATABASE/ARTIST_DB.PY

import datetime

from .. import models, SESSION
from ..logical.utility import GetCurrentTime, ProcessUTCTimestring
from .base_db import UpdateColumnAttributes, UpdateRelationshipCollections, AppendRelationshipCollections

# ##GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['artist_id', 'site_id', 'site_illust_id', 'site_created', 'pages', 'score', 'active']
UPDATE_SCALAR_RELATIONSHIPS = [('tags', 'name', models.Tag)]
APPEND_SCALAR_RELATIONSHIPS = [('commentaries', 'body', models.Description)]


# ## FUNCTIONS


def CreateIllustFromParameters(createparams):
    current_time = GetCurrentTime()
    data = {
        'site_id': createparams['site_id'],
        'site_illust_id': createparams['site_illust_id'],
        'requery': current_time + datetime.timedelta(days=1),
        'artist_id': createparams['artist_id'],
        'pages': createparams['pages'],
        'score': createparams['score'],
        'active': createparams['active'],
        'created': current_time,
        'updated': current_time,
    }
    illust = models.Illust(**data)
    SESSION.add(illust)
    SESSION.commit()
    AddSiteData(illust, createparams) # This needs to be fixed so that it calls the add site data function by source; add a \sources folder and put the db manipulation by source inside
    UpdateRelationshipCollections(illust, UPDATE_SCALAR_RELATIONSHIPS, createparams)
    AppendRelationshipCollections(illust, APPEND_SCALAR_RELATIONSHIPS, createparams)
    return illust

def AddSiteData(illust, params):
    print("AddSiteData")
    data = {
        'illust_id': illust.id,
        'retweets': params['retweets'] if 'retweets' in params else None,
        'replies': params['replies'] if 'replies' in params else None,
        'quotes': params['quotes'] if 'quotes' in params else None,
    }
    site_data = models.TwitterData(**data)
    SESSION.add(site_data)
    SESSION.commit()
