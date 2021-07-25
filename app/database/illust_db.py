# APP/DATABASE/ARTIST_DB.PY

import datetime

from .. import models, SESSION
from ..logical.utility import GetCurrentTime, ProcessUTCTimestring
from .base_db import UpdateColumnAttributes, UpdateRelationshipCollections, AppendRelationshipCollections, SetTimesvalue
from .illust_url_db import UpdateIllustUrlFromParameters
from .site_data_db import UpdateSiteDataFromParameters

# ##GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['artist_id', 'site_id', 'site_illust_id', 'site_created', 'pages', 'score', 'active']
UPDATE_SCALAR_RELATIONSHIPS = [('tags', 'name', models.Tag)]
APPEND_SCALAR_RELATIONSHIPS = [('commentaries', 'body', models.Description)]

CREATE_ALLOWED_ATTRIBUTES = ['artist_id', 'site_id', 'site_illust_id', 'site_created', 'pages', 'score', 'active', 'tags', 'commentaries']
UPDATE_ALLOWED_ATTRIBUTES = ['site_id', 'site_illust_id', 'site_created', 'pages', 'score', 'active', 'tags', 'commentaries']


# ## FUNCTIONS

# #### Helper functions

def SetTimesvalues(params):
    SetTimesvalue(params, 'site_created')
    SetTimesvalue(params, 'site_updated')
    SetTimesvalue(params, 'site_uploaded')


# #### Auxiliary functions

def UpdateIllustUrls(illust, params):
    update_results = []
    existing_urls = [illust_url.url for illust_url in illust.urls]
    current_urls = []
    for url_data in params:
        illust_url = next(filter(lambda x: x.url == url_data['url'], illust.urls), None)
        if illust_url is None:
            illust_url = models.IllustUrl(illust_id=illust.id)
        update_results.append(UpdateIllustUrlFromParameters(illust_url, url_data))
        current_urls.append(url_data['url'])
    removed_urls = set(existing_urls).difference(current_urls)
    for url in removed_urls:
        illust_url = next(filter(lambda x: x.url == url, illust.urls))
        illust_url.active = False
        SESSION.commit()
        update_results.append(True)
    return any(update_results)


# #### Route DB functions

# ###### CREATE

def CreateIllustFromParameters(createparams):
    current_time = GetCurrentTime()
    SetTimesvalues(createparams)
    illust = models.Illust(created=current_time, updated=current_time, requery=(current_time + datetime.timedelta(days=1)))
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    UpdateColumnAttributes(illust, update_columns, createparams)
    create_relationships = [relationship for relationship in UPDATE_SCALAR_RELATIONSHIPS if relationship[0] in settable_keylist]
    UpdateRelationshipCollections(illust, create_relationships, createparams)
    append_relationships = [relationship for relationship in APPEND_SCALAR_RELATIONSHIPS if relationship[0] in settable_keylist]
    AppendRelationshipCollections(illust, append_relationships, createparams)
    UpdateSiteDataFromParameters(illust.site_data, illust.id, illust.site_id, createparams)
    if 'illust_urls' in createparams:
        UpdateIllustUrls(illust, createparams['illust_urls'])
    return illust


# ###### UPDATE

def UpdateIllustFromParameters(illust, updateparams):
    update_results = []
    SetTimesvalues(updateparams)
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(UpdateColumnAttributes(illust, update_columns, updateparams))
    update_relationships = [relationship for relationship in UPDATE_SCALAR_RELATIONSHIPS if relationship[0] in settable_keylist]
    update_results.append(UpdateRelationshipCollections(illust, update_relationships, updateparams))
    append_relationships = [relationship for relationship in APPEND_SCALAR_RELATIONSHIPS if relationship[0] in settable_keylist]
    update_results.append(AppendRelationshipCollections(illust, append_relationships, updateparams))
    update_results.append(UpdateSiteDataFromParameters(illust.site_data, illust.id, illust.site_id, updateparams))
    if 'illust_urls' in updateparams:
        update_results.append(UpdateIllustUrls(illust, updateparams['illust_urls']))
    if any(update_results):
        print("Changes detected.")
        illust.updated = GetCurrentTime()
        SESSION.commit()
    if 'requery' in updateparams:
        illust.requery = updateparams['requery']
        SESSION.commit()
