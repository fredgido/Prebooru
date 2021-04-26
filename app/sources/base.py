# APP/SOURCES/BASE.PY

# ##PYTHON IMPORTS
from ..sources import SOURCES
from ..models import Upload
from ..logical.downloader import DownloadMultipleImages, DownloadSingleImage
from .. import database as DB


# ##FUNCTIONS


def GetSource(request_url, referrer_url):
    for source in SOURCES:
        if source.UploadCheck(request_url, referrer_url):
            return source


def CreateUpload(request_url, referrer_url, image_urls, uploader_id, force):
    source = GetSource(request_url, referrer_url)
    if source is None:
        return {'error': "Not a valid URL."}
    type = source.GetUploadType(request_url)
    upload = None
    valid_image_urls = [url for url in image_urls if source.IsImageUrl(url)]
    print(force, image_urls, valid_image_urls)
    if not force:
        upload = Upload.query.filter_by(type=type, request_url=request_url, referrer_url=referrer_url).order_by(Upload.id.desc()).first()
    if upload is None:
        upload = DB.local.CreateUploadFromRequest(type, request_url, image_urls, uploader_id)
    return upload.to_json()


def ProcessUpload(upload):
    upload.status = 'processing'
    DB.local.SaveData(upload)
    source = GetSource(upload.request_url, upload.referrer_url)
    illust_id = source.GetIllustId(upload.request_url, upload.referrer_url)
    print(source)
    illust, error = source.GetDBIllust(illust_id)
    if error is not None:
        DB.local.AppendError(upload, error)
    if illust is None:
        upload.status = 'error'
        DB.local.CreateAndAppendError('sources.base.ProcessUpload', "Error creating illust record.", upload)
        return
    artist, error = source.GetDBArtist(illust)
    if error is not None:
        DB.local.AppendError(upload, error)
    print(upload, illust, artist)
    if upload.type == 'post' or upload.type == 'subscription':
        DownloadMultipleImages(illust, upload, source)
    elif upload.type == 'image':
        DownloadSingleImage(illust, upload, source)
