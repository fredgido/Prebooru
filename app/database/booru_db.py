# APP/DATABASE/ARTIST_DB.PY

# ##LOCAL IMPORTS
from .. import models, SESSION
from ..logical.utility import GetCurrentTime
from ..sources.base import GetArtistIdSource
from ..sources.danbooru import GetArtistByID, GetArtistUrlsByArtistID
from .base_db import UpdateColumnAttributes, UpdateRelationshipCollections


# ##GLOBAL VARIABLES


COLUMN_ATTRIBUTES = ['danbooru_id', 'current_name']
UPDATE_SCALAR_RELATIONSHIPS = [('names', 'name', models.Label)]
APPEND_SCALAR_RELATIONSHIPS = []


# ## FUNCTIONS

# #### Helper functions


def SetAllNames(params, booru):
    if params['current_name']:
        params['names'] = params['names'] if 'names' in params else [booru_name.name for booru_name in booru.names]
        params['names'] = list(set(params['names'] + [params['current_name']]))


# #### Router helper functions

# ###### Create


def CreateBooruFromParameters(createparams):
    current_time = GetCurrentTime()
    data = {
        'danbooru_id': createparams['danbooru_id'],
        'current_name': createparams['current_name'],
        'created': current_time,
        'updated': current_time,
    }
    booru = models.Booru(**data)
    SESSION.add(booru)
    SESSION.commit()
    UpdateRelationshipCollections(booru, UPDATE_SCALAR_RELATIONSHIPS, createparams)
    return booru


def CreateBooruFromID(danbooru_id):
    data = GetArtistByID(danbooru_id)
    if data['error']:
        return data
    createparams = {
        'danbooru_id': danbooru_id,
        'current_name': data['artist']['name'],
        'names': [data['artist']['name']],
    }
    booru = CreateBooruFromParameters(createparams)
    return {'error': False, 'item': booru.to_json()}


# ###### Update


def UpdateBooruFromParameters(booru, updateparams, updatelist):
    update_results = []
    SetAllNames(updateparams, booru)
    update_columns = set(updatelist).intersection(COLUMN_ATTRIBUTES)
    update_results.append(UpdateColumnAttributes(booru, update_columns, updateparams))
    update_relationships = [relationship for relationship in UPDATE_SCALAR_RELATIONSHIPS if relationship[0] in updatelist]
    update_results.append(UpdateRelationshipCollections(booru, update_relationships, updateparams))
    if any(update_results):
        print("Changes detected.")
        booru.updated = GetCurrentTime()
        SESSION.commit()


def QueryUpdateBooru(booru):
    dirty = False
    booru_data = GetArtistByID(booru.danbooru_id)
    if booru_data['error']:
        return booru_data
    updateparams = {
        'current_name': booru_data['artist']['name'],
    }
    UpdateBooruFromParameters(booru, updateparams, ['current_name'])
    return {'error': False}


# ###### Misc


def CheckArtistsBooru(booru):
    dirty = False
    data = GetArtistByID(booru.danbooru_id, include_urls=True)
    if data['error']:
        return data
    found_artists = {}
    existing_artist_ids = [artist.id for artist in booru.artists]
    artist_urls = [artist_url for artist_url in data['artist']['urls']]
    for artist_url in artist_urls:
        source = GetArtistIdSource(artist_url['url'])
        if source is None:
            continue
        site_artist_id = int(source.GetArtistIdUrlId(artist_url['url']))
        site_id = source.SiteId()
        artist = models.Artist.query.filter_by(site_id=site_id, site_artist_id=site_artist_id).first()
        if artist is None or artist.id in existing_artist_ids:
            continue
        print("Adding artist #", artist.id)
        booru.artists.append(artist)
        SESSION.commit()
        dirty = True
    if dirty:
        booru.updated = GetCurrentTime()
        SESSION.commit()
    return {'error': False}
