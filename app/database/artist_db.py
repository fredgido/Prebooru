# APP/DATABASE/ARTIST_DB.PY

import datetime

from .. import models, SESSION
from ..logical.utility import GetCurrentTime, ProcessUTCTimestring
from .base_db import UpdateColumnAttributes, UpdateRelationshipCollections, AppendRelationshipCollections

# ##GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['site_id', 'site_artist_id', 'current_site_account', 'site_created', 'active']
UPDATE_SCALAR_RELATIONSHIPS = [('site_accounts', 'name', models.Label), ('names', 'name', models.Label)]
APPEND_SCALAR_RELATIONSHIPS = [('profiles', 'body', models.Description)]


# ## FUNCTIONS


def CreateArtistFromParameters(params):
    current_time = GetCurrentTime()
    data = {
        'site_id': params['site_id'],
        'site_artist_id': params['site_artist_id'],
        'current_site_account': params['current_site_account'],
        'site_created': ProcessUTCTimestring(params['site_created']),
        'requery': current_time + datetime.timedelta(days=1),
        'active': params['active'],
        'created': current_time,
        'updated': current_time,
    }
    artist = models.Artist(**data)
    SESSION.add(artist)
    SESSION.commit()
    for name in params['names']:
        AddArtistName(artist, name)
    if params['current_site_account']:
        params['site_accounts'] = list(set(params['site_accounts'] + [params['current_site_account']]))
    for account in params['site_accounts']:
        AddArtistSiteAccount(artist, account)
    if len(params['webpages']):
        AddArtistWebpages(artist, params['webpages'])
    if params['profile']:
        AddArtistProfile(artist, params['profile'])
    return artist


def UpdateArtistFromParameters(artist, updateparams, updatelist):
    update_results = []
    SetTimesvalues(updateparams)
    SetAllSiteAccounts(updateparams)
    update_columns = set(updatelist).intersection(COLUMN_ATTRIBUTES)
    print("#2", update_columns)
    update_results.append(UpdateColumnAttributes(artist, update_columns, updateparams))
    update_relationships = [relationship for relationship in UPDATE_SCALAR_RELATIONSHIPS if relationship[0] in updatelist]
    print("#3", update_relationships)
    update_results.append(UpdateRelationshipCollections(artist, update_relationships, updateparams))
    # This needs to be fixed for profile adds
    append_relationships = [relationship for relationship in APPEND_SCALAR_RELATIONSHIPS if relationship[0] in updatelist]
    print("#3", append_relationships)
    update_results.append(AppendRelationshipCollections(artist, append_relationships, updateparams))
    if 'webpages' in updateparams:
        update_results.append(SetArtistWebpages(artist, updateparams['webpages']))
    # if 'profile' in updateparams:
    #    update_results.append(AddArtistProfile(artist, updateparams['profile']))
    if any(update_results):
        print("Changes detected.")
        artist.updated = GetCurrentTime()
        SESSION.commit()
    if 'requery' in updateparams:
        artist.requery = updateparams['requery']
        SESSION.commit()


def SetTimesvalues(params):
    if 'site_created' in params:
        if type(params['site_created']) is str:
            params['site_created'] = ProcessUTCTimestring(params['site_created'])
        elif type(params['site_created']) is not datetime.datetime:
            params['site_created'] = None


def SetAllSiteAccounts(params):
    if 'current_site_account' in params and params['current_site_account']:
        params['site_accounts'] = list(set(params['site_accounts'] + [params['current_site_account']]))


def SetArtistWebpages(artist, params):
    print("AddArtistWebpages")
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


#################################################################


def AddArtistName(artist, name_text):
    current_names = [label.name for label in artist.names]
    if name_text in current_names:
        return False
    lbl = models.Label.query.filter_by(name=name_text).first()
    if lbl is None:
        lbl = models.Label(name=name_text)
    artist.names.append(lbl)
    SESSION.commit()
    return True


def AddArtistSiteAccount(artist, site_account_text):
    current_site_accounts = [label.name for label in artist.site_accounts]
    if site_account_text in current_site_accounts:
        return False
    lbl = models.Label.query.filter_by(name=site_account_text).first()
    if lbl is None:
        lbl = models.Label(name=site_account_text)
    artist.site_accounts.append(lbl)
    SESSION.commit()
    return True


def AddArtistProfile(artist, profile_text):
    print("AddArtistProfile")
    current_profiles = [descr.body for descr in artist.profiles]
    if profile_text in current_profiles:
        return False
    descr = models.Description.query.filter_by(body=profile_text).first()
    if descr is None:
        descr = models.Description(body=profile_text)
    artist.profiles.append(descr)
    SESSION.commit()
    return True


def AddArtistWebpages(artist, webpages, commit=True):
    print("AddArtistWebpages")
    artist_urls = []
    new_urls = []
    for url in webpages:
        is_active = url[0] != '-'
        if not is_active:
            url = url[1:]
        artist_url = models.ArtistUrl.query.filter_by(artist_id=artist.id, url=url).first()
        if artist_url is None:
            data = {
                'artist_id': artist.id,
                'url': url,
                'active': is_active,
            }
            artist_url = models.ArtistUrl(**data)
            new_urls.append(artist_url)
        artist_urls.append(artist_url)
    if commit and len(new_urls):
        SESSION.add_all(new_urls)
        SESSION.commit()
        print("Added artist webpages:", [webpage.url for webpage in new_urls])
    return artist_urls
