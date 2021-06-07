# APP/SOURCES/BASE.PY

# ##PYTHON IMPORTS
from ..sites import GetSiteKey
from ..sources import SOURCES, DICT as SOURCEDICT
from ..models import Upload, IllustUrl
from ..logical.downloader import DownloadMultipleImages, DownloadSingleImage
from ..logical.uploader import UploadIllustUrl
from ..database import local as DBLOCAL


# ##FUNCTIONS


def GetSource(request_url, referrer_url):
    for source in SOURCES:
        if source.UploadCheck(request_url, referrer_url):
            return source


def GetImageSource(image_url):
    for source in SOURCES:
        if source.IsImageUrl(image_url):
            return source

def CreateUpload(request_url, referrer_url, image_urls, uploader_id, force):
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
        return {'error': False, 'data': DBLOCAL.CreateUploadFromRequest(type, request_url, image_urls, uploader_id).to_json()}
    else:
        return {'error': True, 'message': 'Already uploaded on upload #%d' % upload.id, 'data': upload.to_json()}


def CreateFileUpload(uploader_id, media_filepath, sample_filepath, illust_url_id):
    illust_url = IllustUrl.query.filter_by(id=illust_url_id).first()
    if illust_url is None:
        return {'error': True, 'message': "Illust Url #%d does not exist." % (illust_url_id)}
    elif illust_url.post is not None:
        return {'error': True, 'message': "Illust Url #%d already uploaded as post #%d." % (illust_url.id, illust_url.post.id)}
    else:
        return {'error': False, 'data': DBLOCAL.CreateFileUploadFromRequest(uploader_id, media_filepath, sample_filepath, illust_url_id)}


def ProcessUpload(upload):
    upload.status = 'processing'
    DBLOCAL.SaveData(upload)
    if upload.type == 'post':
        ProcessNetworkUpload(upload)
    elif upload.type == 'file':
        ProcessFileUpload(upload)


def ProcessFileUpload(upload):
    site_id = upload.illust_url and upload.illust_url.illust and upload.illust_url.illust.site_id
    if site_id is None:
        DBLOCAL.CreateAndAppendError('sources.base.ProcessFileUpload', "No site ID found through illust url.", upload)
        upload.status = 'error'
        DBLOCAL.SaveData(upload)
        return
    source = _Source(site_id)
    if UploadIllustUrl(upload, source):
        upload.status = 'complete'
    else:
        upload.status = 'error'
    DBLOCAL.SaveData(upload)


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

def ProcessArtist(artist):
    source = _Source(artist.site_id)
    source.UpdateDBArtist(artist)


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
