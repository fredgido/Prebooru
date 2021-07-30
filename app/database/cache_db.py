# APP/DATABASE/CACHE_DB.PY

# ##LOCAL IMPORTS
from .. import SESSION
from ..logical.utility import GetCurrentTime, DaysFromNow
from ..cache import ApiData


# ##FUNCTIONS


def GetApiData(data_ids, site_id, type):
    cache_data = []
    for i in range(0, len(data_ids), 100):
        sublist = data_ids[i: i + 100]
        cache_data += _GetApiData(sublist, site_id, type)
    return cache_data


def GetApiArtist(site_artist_id, site_id):
    cache = GetApiData([site_artist_id], site_id, 'artist')
    return cache[0].data if len(cache) else None


def GetApiIllust(site_illust_id, site_id):
    cache = GetApiData([site_illust_id], site_id, 'illust')
    return cache[0].data if len(cache) else None


def SaveApiData(network_data, id_key, site_id, type):
    data_ids = [int(data[id_key]) for data in network_data]
    cache_data = GetApiData(data_ids, site_id, type)
    for data_item in network_data:
        data_id = int(data_item[id_key])
        cache_item = next(filter(lambda x: x.data_id == data_id, cache_data), None)
        if not cache_item:
            data = {
                'site_id': site_id,
                'type': type,
                'data_id': data_id,
            }
            cache_item = ApiData(**data)
            SESSION.add(cache_item)
        else:
            print("SaveApiData - updating cache item:", type, data_id, cache_item.id)
        cache_item.data = data_item
        cache_item.expires = DaysFromNow(1)
    SESSION.commit()


# #### Private functions


def _GetApiData(data_ids, site_id, type):
    q = ApiData.query
    q = q.filter_by(site_id=site_id, type=type)
    if len(data_ids) == 1:
        q = q.filter_by(data_id=data_ids[0])
    else:
        q = q.filter(ApiData.data_id.in_(data_ids))
    q = q.filter(ApiData.expires > GetCurrentTime())
    return q.all()
