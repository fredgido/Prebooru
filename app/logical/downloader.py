# APP/LOGICAL/DOWNLOADER.PY

# ##PYTHON IMPORTS
import requests
from PIL import Image
from io import BytesIO

# ##LOCAL IMPORTS
from .utility import GetHTTPFilename, GetFileExtension, GetBufferChecksum
from .file import PutGetRaw, CreateDirectory
from .network import GetHTTPFile
from .. import database as DB
from ..config import workingdirectory, imagefilepath
from .. import sites
from .. import data

# ##GLOBAL VARIABLES

ONE_DAY = 60 * 60 * 24

FORMAT_EXT = {
    'PNG': 'png',
    'JPEG': 'jpg',
    'GIF': 'gif',
}

# ##FUNCTIONS


def DownloadMultipleImages(illust, upload, source):
    all_upload_urls = [source.NormalizeImageURL(upload_url.url) for upload_url in upload.image_urls]
    print("DownloadMultipleImages", all_upload_urls)
    for illust_url in illust.urls:
        if len(all_upload_urls) == 0 or illust_url.url in all_upload_urls:
            DownloadAndRecordOutcome(illust_url, upload, source)
    upload.status = 'complete'
    DB.local.SaveData(upload)


def DownloadSingleImage(illust, upload, source):
    image_url = source.NormalizeImageURL(upload.request)
    for illust_url in illust.urls:
        if image_url == illlust_url.url:
            DownloadAndRecordOutcome(illust_url, upload, source)
            upload.status = 'complete'
            DB.local.SaveData(upload)
            return
    DB.local.CreateAndAppendError('utility.downloader.DownloadSingleImage', "Unable to find submitted image URL %s on illust #%d." % (image_url, illust.id), upload)
    upload.status = 'error'
    DB.local.SaveData(upload)


def DownloadAndRecordOutcome(illust_url, upload, source):
    post = DownloadImage(illust_url, source)
    if isinstance(post, DB.models.Error):
        DB.local.AppendError(upload, post)
        upload.failures += 1
    else:
        upload.posts.append(post)
        upload.successes += 1


def CreatePreview(image, md5):
    print("Creating preview:", md5)
    try:
        preview = image.copy().convert("RGB")
        preview.thumbnail(data.PREVIEW_DIMENSIONS)
        filepath = data.DataDirectory('preview', md5) + md5 + '.jpg'
        CreateDirectory(filepath)
        preview.save(filepath, "JPEG")
    except Exception as e:
        return DB.local.CreateError('utility.downloader.CreatePreview', "Error creating preview: %s" % repr(e))


def CreateSample(image, md5):
    print("Creating sample:", md5)
    try:
        sample = image.copy().convert("RGB")
        sample.thumbnail(data.SAMPLE_DIMENSIONS)
        filepath = data.DataDirectory('sample', md5) + md5 + '.jpg'
        CreateDirectory(filepath)
        sample.save(filepath, "JPEG")
    except Exception as e:
        return DB.local.CreateError('utility.downloader.CreateSample', "Error creating sample: %s" % repr(e))


def CreateData(image, md5, file_ext):
    print("Saving data:", md5)
    filepath = data.DataDirectory('data', md5) + md5 + '.' + file_ext
    CreateDirectory(filepath)
    image.save(filepath)


def DownloadImage(illust_url, source):
    download_url = source.GetFullUrl(illust_url)
    file_ext = source.GetImageExtension(download_url)
    if file_ext not in ['jpg', 'png']:
        return DB.local.CreateError('utility.downloader.DownloadImage', "Unsupported file format: %s" % file_ext)
    print("Downloading", download_url)
    buffer = GetHTTPFile(download_url, headers=source.IMAGE_HEADERS)
    if isinstance(buffer, Exception):
        return DB.local.CreateError('utility.downloader.DownloadImage', str(buffer))
    if isinstance(buffer, requests.Response):
        return DB.local.CreateError('utility.downloader.DownloadImage', "HTTP %d - %s" % (buffer.status_code, buffer.reason))
    md5 = GetBufferChecksum(buffer)
    post = DB.local.GetDBPostByField('md5', md5)
    if post is not None:
        return DB.local.CreateError('utility.downloader.DownloadImage', "Image already uploaded on post #%d" % post.id)
    try:
        file_imgdata = BytesIO(buffer)
        image = Image.open(file_imgdata)
    except Exception as e:
        return DB.local.CreateError('utility.downloader.DownloadImage', "Error processing image data.")
    
    try:
        CreateData(image, md5, file_ext)
    except Exception:
        return DB.local.CreateError('utility.downloader.DownloadImage', "Error saving image to disk.")
    
    post_errors = []
    if data.HasPreview(data.width, data.height):
        error = CreatePreview(image, md5)
        if error is not None:
            post_errors.append(error)
    if data.HasSample(data.width, data.height):
        error = CreateSample(image, md5)
        if error is not None:
            post_errors.append(error)
    file_ext = FORMAT_EXT[image.format]
    
    if (illust_url.width and image.width != illust_url.width) or (illust_url.height and image.height != illust_url.height):
        post_errors.append(DB.local.CreateError('utility.downloader.DownloadImage', "Mismatching image dimensions: Reported - %d x %d, Actual - %d x %d" % (illust_url.width, illust_url.height, image.width, image.height)))
    
    """
    filepath = data.DataDirectory('data', md5) + md5 + '.' + file_ext
    print("Saving", filepath)
    if PutGetRaw(filepath, 'wb', buffer) < 0:
        return DB.local.CreateError('utility.downloader.DownloadImage', "Error saving image to disk.")
    """
    post = DB.local.CreatePostAndAddIllustUrl(illust_url, image.width, image.height, file_ext, md5, len(buffer))
    if len(post_errors):
        post.errors.extend(post_errors)
        DB.local.SaveData(post)
    return post
