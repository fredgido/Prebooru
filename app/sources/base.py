# APP/SOURCES/BASE.PY

# ##PYTHON IMPORTS
from ..sites import GetSiteKey
from ..sources import SOURCES, DICT as SOURCEDICT
from ..models import Upload
from ..logical.downloader import DownloadMultipleImages, DownloadSingleImage
from ..database import local as DBLOCAL


# ##FUNCTIONS


def GetSource(request_url, referrer_url):
    for source in SOURCES:
        if source.UploadCheck(request_url, referrer_url):
            return source


def CreateUpload(request_url, referrer_url, image_urls, uploader_id, force):
    source = GetSource(request_url, referrer_url)
    if source is None:
        return {'error': True, 'message': "Not a valid URL."}
    type = source.GetUploadType(request_url)
    upload = None
    valid_image_urls = [url for url in image_urls if source.IsImageUrl(url)]
    print(force, image_urls, valid_image_urls)
    if not force:
        upload = Upload.query.filter_by(type=type, request_url=request_url, referrer_url=referrer_url).order_by(Upload.id.desc()).first()
    if upload is None:
        return {'error': False, 'data': DBLOCAL.CreateUploadFromRequest(type, request_url, image_urls, uploader_id).to_json()}
    else:
        return {'error': True, 'message': 'Already uploaded on upload #%d' % upload.id, 'data': upload.to_json()}


def ProcessUpload(upload):
    upload.status = 'processing'
    DBLOCAL.SaveData(upload)
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

    print(upload, illust, artist)
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


def CreateNewArtist(site_id, site_artist_id):
    source = GetSource(site_id)
    source.CreateDBArtist(site_artist_id)

