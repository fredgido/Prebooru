# APP/LOGICAL/DOWNLOADER.PY

# ##PYTHON IMPORTS
import requests
from PIL import Image
from io import BytesIO

# ##LOCAL IMPORTS
from .utility import GetBufferChecksum
from .file import CreateDirectory
from .network import GetHTTPFile
from .. import database as DB
from .. import storage

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
        if image_url == illust_url.url:
            DownloadAndRecordOutcome(illust_url, upload, source)
            upload.status = 'complete'
            DB.local.SaveData(upload)
            return
    DB.local.CreateAndAppendError('utility.downloader.DownloadSingleImage', "Unable to find submitted image URL %s on illust #%d." % (image_url, illust.id), upload)
    upload.status = 'error'
    DB.local.SaveData(upload)


def DownloadAndRecordOutcome(illust_url, upload, source):
    post = ProcessDownload(illust_url, source)
    if DB.local.IsError(post):
        DB.local.AppendError(upload, post)
        upload.failures += 1
    else:
        upload.posts.append(post)
        upload.successes += 1


def CreatePreview(image, md5):
    print("Creating preview:", md5)
    try:
        preview = image.copy().convert("RGB")
        preview.thumbnail(storage.PREVIEW_DIMENSIONS)
        filepath = storage.DataDirectory('preview', md5) + md5 + '.jpg'
        CreateDirectory(filepath)
        print("Saving preview:", filepath)
        preview.save(filepath, "JPEG")
    except Exception as e:
        return DB.local.CreateError('utility.downloader.CreatePreview', "Error creating preview: %s" % repr(e))


def CreateSample(image, md5):
    print("Creating sample:", md5)
    try:
        sample = image.copy().convert("RGB")
        sample.thumbnail(storage.SAMPLE_DIMENSIONS)
        filepath = storage.DataDirectory('sample', md5) + md5 + '.jpg'
        CreateDirectory(filepath)
        print("Saving sample:", filepath)
        sample.save(filepath, "JPEG")
    except Exception as e:
        return DB.local.CreateError('utility.downloader.CreateSample', "Error creating sample: %s" % repr(e))


def CreateData(image, md5, file_ext):
    print("Saving data:", md5)
    filepath = storage.DataDirectory('data', md5) + md5 + '.' + file_ext
    CreateDirectory(filepath)
    print("Saving data:", filepath)
    image.save(filepath)


def DownloadImage(illust_url, source):
    download_url = source.GetFullUrl(illust_url)
    file_ext = source.GetImageExtension(download_url)
    if file_ext not in ['jpg', 'png']:
        return DB.local.CreateError('utility.downloader.ProcessDownload', "Unsupported file format: %s" % file_ext), None
    print("Downloading", download_url)
    buffer = GetHTTPFile(download_url, headers=source.IMAGE_HEADERS)
    if isinstance(buffer, Exception):
        return DB.local.CreateError('utility.downloader.ProcessDownload', str(buffer)), None
    if isinstance(buffer, requests.Response):
        return DB.local.CreateError('utility.downloader.ProcessDownload', "HTTP %d - %s" % (buffer.status_code, buffer.reason)), None
    return buffer, file_ext


def CheckImage(buffer, illust_url):
    md5 = GetBufferChecksum(buffer)
    post = DB.local.GetDBPostByField('md5', md5)
    if post is not None:
        post.illust_urls.append(illust_url)
        DB.local.SaveData(post)
        return DB.local.CreateError('utility.downloader.ProcessDownload', "Image already uploaded on post #%d" % post.id), None
    try:
        file_imgdata = BytesIO(buffer)
        image = Image.open(file_imgdata)
    except Exception as e:
        return DB.local.CreateError('utility.downloader.ProcessDownload', "Error processing image data: %s" % repr(e)), None
    return image, md5


def SaveImage(image, md5, file_ext, illust_url):
    image_file_ext = FORMAT_EXT[image.format]
    try:
        CreateData(image, md5, image_file_ext)
    except Exception as e:
        return DB.local.CreateError('utility.downloader.ProcessDownload', "Error saving image to disk: %s" % repr(e)), None
    post_errors = []
    if storage.HasPreview(image.width, image.height):
        error = CreatePreview(image, md5)
        if error is not None:
            post_errors.append(error)
    if storage.HasSample(image.width, image.height):
        error = CreateSample(image, md5)
        if error is not None:
            post_errors.append(error)
    if file_ext != image_file_ext:
        error = DB.local.CreateError('utility.downloader.SaveImage', "Mismatching file extensions: Reported - %s, Actual - %s" % (image_file_ext, file_ext))
        post_errors.append(error)
    if (illust_url.width and image.width != illust_url.width) or (illust_url.height and image.height != illust_url.height):
        error = DB.local.CreateError('utility.downloader.ProcessDownload', "Mismatching image dimensions: Reported - %d x %d, Actual - %d x %d" % (illust_url.width, illust_url.height, image.width, image.height))
        post_errors.append(error)
    return post_errors, image_file_ext


def ProcessDownload(illust_url, source):
    buffer, file_ext = DownloadImage(illust_url, source)
    if DB.local.IsError(buffer):
        return buffer
    image, md5 = CheckImage(buffer, illust_url)
    if DB.local.IsError(image):
        return image
    post_errors, image_file_ext = SaveImage(image, md5, file_ext, illust_url)
    if DB.local.IsError(post_errors):
        return post_errors
    post = DB.local.CreatePostAndAddIllustUrl(illust_url, image.width, image.height, image_file_ext, md5, len(buffer))
    if len(post_errors):
        post.errors.extend(post_errors)
        DB.local.SaveData(post)
    return post
