# APP/DATABASE/ARTIST_DB.PY

import datetime

from .. import models, SESSION
from ..logical.utility import GetCurrentTime, ProcessUTCTimestring
from ..sites import Site
from .base_db import UpdateColumnAttributes, UpdateRelationshipCollections, AppendRelationshipCollections
from .illust_url_db import UpdateIllustUrlFromParameters
from .site_data_db import UpdateSiteDataFromParameters

# ##GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['artist_id', 'site_id', 'site_illust_id', 'site_created', 'pages', 'score', 'active']
UPDATE_SCALAR_RELATIONSHIPS = [('tags', 'name', models.Tag)]
APPEND_SCALAR_RELATIONSHIPS = [('commentaries', 'body', models.Description)]

TWITTER_COLUMN_ATTRIBUTES = ['retweets', 'replies', 'quotes']

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


def UpdateIllustFromParameters(illust, updateparams, updatelist):
    update_results = []
    SetTimesvalues(updateparams)
    update_columns = set(updatelist).intersection(COLUMN_ATTRIBUTES)
    print("UpdateIllustFromParameters", update_columns, updateparams)
    update_results.append(UpdateColumnAttributes(illust, update_columns, updateparams))
    update_relationships = [relationship for relationship in UPDATE_SCALAR_RELATIONSHIPS if relationship[0] in updatelist]
    update_results.append(UpdateRelationshipCollections(illust, update_relationships, updateparams))
    append_relationships = [relationship for relationship in APPEND_SCALAR_RELATIONSHIPS if relationship[0] in updatelist]
    update_results.append(AppendRelationshipCollections(illust, append_relationships, updateparams))
    update_results.append(UpdateSiteDataFromParameters(illust.site_data, illust.id, illust.site_id, updateparams, updatelist))
    if 'illust_urls' in updateparams:
        update_results.append(UpdateIllustUrls(illust, updateparams['illust_urls']))
    if any(update_results):
        print("Changes detected.")
        illust.updated = GetCurrentTime()
        SESSION.commit()
    if 'requery' in updateparams:
        illust.requery = updateparams['requery']
        SESSION.commit()


def SetTimesvalues(params):
    if 'site_created' in params:
        if type(params['site_created']) is str:
            params['site_created'] = ProcessUTCTimestring(params['site_created'])
        elif type(params['site_created']) is not datetime.datetime:
            params['site_created'] = None


def UpdateIllustUrls(illust, params):
    update_results = []
    existing_urls = [illust_url.url for illust_url in illust.urls]
    current_urls = []
    for url_data in params:
        illust_url = next(filter(lambda x: x.url == url_data['url'], illust.urls), None)
        if illust_url is None:
            illust_url = models.IllustUrl(illust_id=illust.id)
        update_results.append(UpdateIllustUrlFromParameters(illust_url, url_data, list(url_data.keys())))
        current_urls.append(url_data['url'])
    removed_urls = set(existing_urls).difference(current_urls)
    for url in removed_urls:
        illust_url = next(filter(lambda x: x.url == url, illust.urls))
        illust_url.active = False
        SESSION.commit()
        update_results.append(True)
    return any(update_results)
