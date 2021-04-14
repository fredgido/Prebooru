from ..sources import SOURCES
from .. import database as DB


def UploadCheck(request_url):
    for source in SOURCES:
        if source.UploadCheck(request_url):
            return source
    return {'error': "Not a valid URL!"}


def ProcessUpload(request_url, uploader_id):
    source = UploadCheck(request_url)
    if isinstance(source, str):
        return source
    type = source.GetUploadType(request_url)
    upload = DB.local.CreateUploadFromRequest(type, request_url, uploader_id)
    source.DownloadIllust(type, upload)
    

