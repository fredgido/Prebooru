# APP/DATABASE/ARTIST_DB.PY

import datetime

from .. import models, SESSION
from ..logical.utility import GetCurrentTime, ProcessUTCTimestring
from .base_db import UpdateColumnAttributes, UpdateRelationshipCollections, AppendRelationshipCollections

# ##GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['site_id', 'site_artist_id', 'current_site_account', 'site_created', 'active']
UPDATE_SCALAR_RELATIONSHIPS = [('site_accounts', 'name', models.Label), ('names', 'name', models.Label)]
APPEND_SCALAR_RELATIONSHIPS = [('profiles', 'body', models.Description)]

CREATE_ALLOWED_ATTRIBUTES = ['site_id', 'site_artist_id', 'current_site_account', 'site_created', 'active', 'site_accounts', 'names', 'profiles']
UPDATE_ALLOWED_ATTRIBUTES = ['site_id', 'site_artist_id', 'current_site_account', 'site_created', 'active', 'site_accounts', 'names', 'profiles']


# ## FUNCTIONS

# #### Helper functions


def SetTimesvalues(params):
    if 'site_created' in params:
        if type(params['site_created']) is str:
            params['site_created'] = ProcessUTCTimestring(params['site_created'])
        elif type(params['site_created']) is not datetime.datetime:
            params['site_created'] = None


def SetAllSiteAccounts(params):
    if 'current_site_account' in params and params['current_site_account']:
        params['site_accounts'] = list(set(params['site_accounts'] + [params['current_site_account']]))


# #### Auxiliary functions


def UpdateArtistWebpages(artist, params):
    existing_webpages = [webpage.url for webpage in artist.webpages]
    current_webpages = []
    is_dirty = False
    for url in params:
        is_active = url[0] != '-'
        if not is_active:
            url = url[1:]
        artist_url = next(filter(lambda x: x.url == url, artist.webpages), None)
        if artist_url is None:
            data = {
                'artist_id': artist.id,
                'url': url,
                'active': is_active,
            }
            artist_url = models.ArtistUrl(**data)
            SESSION.add(artist_url)
            is_dirty = True
        elif artist_url.active != is_active:
            artist_url.active = is_active
            is_dirty = True
        current_webpages.append(url)
    removed_webpages = set(existing_webpages).difference(current_webpages)
    for url in removed_webpages:
        # These will only be removable from the edit artist interface
        artist_url = next(filter(lambda x: x.url == url, artist.webpages))
        SESSION.delete(artist_url)
        is_dirty = True
    if is_dirty:
        SESSION.commit()
    return is_dirty


# #### Route DB functions

# ###### Create


def CreateArtistFromParameters(createparams):
    current_time = GetCurrentTime()
    SetTimesvalues(createparams)
    SetAllSiteAccounts(createparams)
    artist = models.Artist(created=current_time, updated=current_time, requery=(current_time + datetime.timedelta(days=1)))
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    UpdateColumnAttributes(artist, update_columns, createparams)
    create_relationships = [relationship for relationship in UPDATE_SCALAR_RELATIONSHIPS if relationship[0] in settable_keylist]
    UpdateRelationshipCollections(artist, create_relationships, createparams)
    append_relationships = [relationship for relationship in APPEND_SCALAR_RELATIONSHIPS if relationship[0] in settable_keylist]
    AppendRelationshipCollections(artist, append_relationships, createparams)
    if 'webpages' in createparams:
        print(artist, createparams['webpages'])
        UpdateArtistWebpages(artist, createparams['webpages'])
    return artist


# ###### Update


def UpdateArtistFromParameters(artist, updateparams):
    update_results = []
    SetTimesvalues(updateparams)
    SetAllSiteAccounts(updateparams)
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(UpdateColumnAttributes(artist, update_columns, updateparams))
    update_relationships = [relationship for relationship in UPDATE_SCALAR_RELATIONSHIPS if relationship[0] in settable_keylist]
    update_results.append(UpdateRelationshipCollections(artist, update_relationships, updateparams))
    append_relationships = [relationship for relationship in APPEND_SCALAR_RELATIONSHIPS if relationship[0] in settable_keylist]
    update_results.append(AppendRelationshipCollections(artist, append_relationships, updateparams))
    if 'webpages' in updateparams:
        update_results.append(UpdateArtistWebpages(artist, updateparams['webpages']))
    if any(update_results):
        print("Changes detected.")
        artist.updated = GetCurrentTime()
        SESSION.commit()
    if 'requery' in updateparams:
        artist.requery = updateparams['requery']
        SESSION.commit()
