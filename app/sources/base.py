# APP/SOURCES/BASE.PY

# ##PYTHON IMPORTS
import sys


from ..sites import GetSiteKey
from ..sources import SOURCES, DICT as SOURCEDICT, danbooru
from ..models import Upload, IllustUrl, Booru, Label
from ..logical.downloader import DownloadMultipleImages, DownloadSingleImage
from ..logical.uploader import UploadIllustUrl
from ..logical.utility import GetHTTPFilename, GetFileExtension, GetCurrentTime
from ..database import local as DBLOCAL

CURRENT_MODULE = sys.modules[__name__]

#print(__name__, __package__, CURRENT_MODULE)

IMAGE_HEADERS = {}

# ##FUNCTIONS


def GetSource(request_url, referrer_url):
    for source in SOURCES:
        if source.UploadCheck(request_url, referrer_url):
            return source


def GetArtistSource(artist_url):
    for source in SOURCES:
        if source.IsArtistUrl(artist_url):
            return source


def GetImageSource(image_url):
    for source in SOURCES:
        if source.IsImageUrl(image_url):
            return source
    return CURRENT_MODULE

def SmallImageUrl(image_url):
    return image_url

def NormalizedImageUrl(image_url):
    return image_url

def GetImageExtension(image_url):
    filename = GetHTTPFilename(image_url)
    return GetFileExtension(filename)

def GetMediaExtension(media_url):
    return GetImageExtension(media_url)

def CreateUpload(request_url, referrer_url, image_urls, force):
    source = GetSource(request_url, referrer_url)
    if source is None:
        return {'error': True, 'message': "Not a valid URL."}
    type = source.GetUploadType(request_url)
    upload = None
    valid_image_urls = [url for url in image_urls if source.IsImageUrl(url)]
    #print(force, image_urls, valid_image_urls)
    if not force:
        upload = Upload.query.filter_by(type=type, request_url=request_url, referrer_url=referrer_url).order_by(Upload.id.desc()).first()
    if upload is None:
        return {'error': False, 'data': DBLOCAL.CreateUploadFromRequest(type, request_url, image_urls).to_json()}
    else:
        return {'error': True, 'message': 'Already uploaded on upload #%d' % upload.id, 'data': upload.to_json()}


def CreateFileUpload(media_filepath, sample_filepath, illust_url_id):
    illust_url = IllustUrl.query.filter_by(id=illust_url_id).first()
    if illust_url is None:
        return {'error': True, 'message': "Illust Url #%d does not exist." % (illust_url_id)}
    elif illust_url.post is not None:
        return {'error': True, 'message': "Illust Url #%d already uploaded as post #%d." % (illust_url.id, illust_url.post.id)}
    else:
        return {'error': False, 'data': DBLOCAL.CreateFileUploadFromRequest(media_filepath, sample_filepath, illust_url_id)}


def ProcessUpload(upload):
    upload.status = 'processing'
    DBLOCAL.SaveData()
    if upload.type == 'post':
        ProcessNetworkUpload(upload)
    elif upload.type == 'file':
        ProcessFileUpload(upload)


def ProcessFileUpload(upload):
    site_id = upload.illust_url and upload.illust_url.illust and upload.illust_url.illust.site_id
    if site_id is None:
        DBLOCAL.CreateAndAppendError('sources.base.ProcessFileUpload', "No site ID found through illust url.", upload)
        upload.status = 'error'
        DBLOCAL.SaveData()
        return
    source = _Source(site_id)
    if UploadIllustUrl(upload, source):
        upload.status = 'complete'
    else:
        upload.status = 'error'
    DBLOCAL.SaveData()


def ProcessNetworkUpload(upload):
    source = GetSource(upload.request_url, upload.referrer_url)
    site_illust_id = source.GetIllustId(upload.request_url, upload.referrer_url)
    error = source.Prework(site_illust_id)
    if error is not None:
        DBLOCAL.AppendError(upload, error)
    illust = source.DB.GetSiteIllust(site_illust_id)
    if illust is None:
        illust = source.CreateIllust(site_illust_id)
        if DBLOCAL.IsError(illust):
            upload.status = 'error'
            DBLOCAL.AppendError(upload, illust)
            return
    elif DBLOCAL.CheckRequery(illust):
        source.UpdateIllust(illust)
    artist = DBLOCAL.GetArtist(illust.artist_id)
    if DBLOCAL.CheckRequery(artist):
        source.UpdateArtist(artist)

    #print(upload, illust, artist)
    if upload.type == 'post' or upload.type == 'subscription':
        DownloadMultipleImages(illust, upload, source)
    elif upload.type == 'image':
        DownloadSingleImage(illust, upload, source)

def _Source(site_id):
    site_key = GetSiteKey(site_id)
    return SOURCEDICT[site_key]

def QueryArtistBoorus(artist):
    source = _Source(artist.site_id)
    search_url = source.ArtistBooruSearchUrl(artist)
    artist_data = danbooru.GetArtistsByUrl(search_url)
    if artist_data['error']:
        return artist_data
    existing_booru_ids = [booru.id for booru in artist.boorus]
    boorus = []
    for danbooru_artist in artist_data['artists']:
        dirty = False
        current_time = GetCurrentTime()
        booru = Booru.query.filter_by(danbooru_id=danbooru_artist['id']).first()
        if booru is None:
            booru = Booru(danbooru_id=danbooru_artist['id'], current_name=danbooru_artist['name'], created=current_time, updated=current_time)
            DBLOCAL.SaveData(booru)
        existing_names = [booru_name.name for booru_name in booru.names]
        if danbooru_artist['name'] not in existing_names:
            dirty = True
            label = Label.query.filter_by(name=danbooru_artist['name']).first()
            if label is None:
                label = Label(name=danbooru_artist['name'])
                DBLOCAL.SaveData(label)
            booru.names.append(label)
        if booru.id not in existing_booru_ids:
            dirty = True
            booru.artists.append(artist)
        if dirty:
            booru.updated = current_time
            DBLOCAL.SaveData()
        boorus.append(booru)
    return {'error': False, 'artist': artist, 'boorus': boorus}

def ProcessArtist(artist):
    source = _Source(artist.site_id)
    source.UpdateDBArtist(artist)


def UpdateArtist(artist):
    source = _Source(artist.site_id)
    source.UpdateArtist(artist)

def UpdateIllust(artist):
    source = _Source(artist.site_id)
    source.UpdateIllust(artist)

def QueryCreateArtist(site_id, site_artist_id):
    source = _Source(site_id)
    return source.CreateArtist(site_artist_id)

def CreateNewArtist(site_id, site_artist_id):
    source = GetSource(site_id)
    source.CreateDBArtist(site_artist_id)

def CreateDBArtistFromParams(params):
    source = _Source(params['site_id'])
    return source.CreateDBArtistFromParams(params)

def CreateDBIllustFromParams(params):
    source = _Source(params['site_id'])
    return source.CreateDBIllustFromParams(params)

def CreateDBIllustUrlFromParams(params, illust):
    source = _Source(illust.site_id)
    return source.CreateDBIllustUrlFromParams(params, illust)
