# APP/LOGICAL/DOWNLOADER.PY

# ##PYTHON IMPORTS
import ffmpeg
import requests
import filetype
from PIL import Image
from io import BytesIO

# ##LOCAL IMPORTS
from .utility import GetBufferChecksum
from .file import CreateDirectory, PutGetRaw
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
    no_media = False
    if source.IllustHasVideos(illust):
        video_illust_url, thumb_illust_url = source.VideoIllustDownloadUrls(illust)
        if thumb_illust_url is None:
            DB.local.CreateAndAppendError('DownloadMultipleImages', "Did not find thumbnail for video on illust #%d" % illust.id, upload)
        else:
            post = CreateVideoPost(video_illust_url, thumb_illust_url, source)
            RecordOutcome(post, upload)
    elif source.IllustHasImages(illust):
        all_upload_urls = [source.NormalizeImageURL(upload_url.url) for upload_url in upload.image_urls]
        image_illust_urls = source.ImageIllustDownloadUrls(illust)
        #print(all_upload_urls, image_illust_urls)
        for illust_url in image_illust_urls:
            #if len(all_upload_urls) > 0:
                #print(all_upload_urls, illust_url.url, illust_url.url in all_upload_urls)
            if len(all_upload_urls) == 0 or illust_url.url in all_upload_urls:
                post = CreateImagePost(illust_url, source)
                RecordOutcome(post, upload)
    else:
        no_media = True
    if no_media or (len(upload.posts) == 0 and len(upload.errors) == 0):
        DB.local.CreateAndAppendError('DownloadMultipleImages', "Did not find any media to download for illust #%d" % illust.id, upload)
    upload.status = 'complete'
    DB.local.SaveData()


def RecordOutcome(post, upload):
    if isinstance(post, list):
        valid_errors = [error for error in post if DB.local.IsError(error)]
        if len(valid_errors) != len(post):
            print("Invalid data returned in outcome:", [item for item in post if not DB.local.IsError(item)])
        upload.errors.extend(valid_errors)
        upload.failures += 1
    else:
        upload.posts.append(post)
        upload.successes += 1
    DB.local.SaveData()


def DownloadSingleImage(illust, upload, source):
    image_url = source.NormalizeImageURL(upload.request)
    for illust_url in illust.urls:
        if image_url == illust_url.url:
            DownloadAndRecordOutcome(illust_url, upload, source)
            upload.status = 'complete'
            DB.local.SaveData()
            return
    DB.local.CreateAndAppendError('utility.downloader.DownloadSingleImage', "Unable to find submitted image URL %s on illust #%d." % (image_url, illust.id), upload)
    upload.status = 'error'
    DB.local.SaveData()


def DownloadAndRecordOutcome(process_func, upload, *args):
    post = process_func(*args)
    if DB.local.IsError(post):
        DB.local.AppendError(upload, post)
        upload.failures += 1
    else:
        upload.posts.append(post)
        upload.successes += 1


def CreatePreview(image, md5, downsample=True):
    print("Creating preview:", image, md5)
    try:
        preview = image.copy().convert("RGB")
        if downsample:
            preview.thumbnail(storage.PREVIEW_DIMENSIONS)
        filepath = storage.DataDirectory('preview', md5) + md5 + '.jpg'
        CreateDirectory(filepath)
        print("Saving preview:", filepath)
        preview.save(filepath, "JPEG")
    except Exception as e:
        return DB.local.CreateError('utility.downloader.CreatePreview', "Error creating preview: %s" % repr(e))


def CreateSample(image, md5, downsample=True):
    print("Creating sample:", md5)
    try:
        sample = image.copy().convert("RGB")
        if downsample:
            sample.thumbnail(storage.SAMPLE_DIMENSIONS)
        filepath = storage.DataDirectory('sample', md5) + md5 + '.jpg'
        CreateDirectory(filepath)
        print("Saving sample:", filepath)
        sample.save(filepath, "JPEG")
    except Exception as e:
        return DB.local.CreateError('utility.downloader.CreateSample', "Error creating sample: %s" % repr(e))


def CreateData(buffer, md5, file_ext):
    print("Saving data:", md5)
    filepath = storage.DataDirectory('data', md5) + md5 + '.' + file_ext
    CreateDirectory(filepath)
    print("Saving data:", filepath)
    PutGetRaw(filepath, 'wb', buffer)


def CreateVideo(buffer, md5, file_ext):
    print("Saving video:", md5)
    filepath = storage.DataDirectory('data', md5) + md5 + '.' + file_ext
    CreateDirectory(filepath)
    print("Saving data:", filepath)
    PutGetRaw(filepath, 'wb', buffer)
    return filepath


def DownloadMedia(illust_url, source):
    download_url = source.GetFullUrl(illust_url)
    file_ext = source.GetMediaExtension(download_url)
    if file_ext not in ['jpg', 'png', 'mp4']:
        return DB.local.CreateError('utility.downloader.ProcessImageDownload', "Unsupported file format: %s" % file_ext), None
    print("Downloading", download_url)
    buffer = GetHTTPFile(download_url, headers=source.IMAGE_HEADERS)
    if isinstance(buffer, Exception):
        return DB.local.CreateError('utility.downloader.ProcessImageDownload', str(buffer)), None
    if isinstance(buffer, requests.Response):
        return DB.local.CreateError('utility.downloader.ProcessImageDownload', "HTTP %d - %s" % (buffer.status_code, buffer.reason)), None
    return buffer, file_ext


def CheckExisting(buffer, illust_url):
    md5 = GetBufferChecksum(buffer)
    post = DB.local.GetDBPostByField('md5', md5)
    if post is not None:
        post.illust_urls.append(illust_url)
        DB.local.SaveData()
        return DB.local.CreateError('utility.downloader.ProcessImageDownload', "Image already uploaded on post #%d" % post.id)
    return md5


def CreatePostError(module, message, post_errors):
    error = DB.local.CreateError(module, message)
    post_errors.append(error)


def LoadImage(buffer):
    try:
        file_imgdata = BytesIO(buffer)
        image = Image.open(file_imgdata)
    except Exception as e:
        return DB.local.CreateError('utility.downloader.ProcessImageDownload', "Error processing image data: %s" % repr(e))
    return image


def CheckFiletype(buffer, file_ext, post_errors):
    try:
        guess = filetype.guess(buffer)
    except Exception as e:
        CreatePostError('utility.downloader.CheckFiletype', "Error reading file headers: %s" % repr(e), post_errors)
        return file_ext
    if guess.extension != file_ext:
        CreatePostError('utility.downloader.CheckFiletype', "Mismatching file extensions: Reported - %s, Actual - %s" % (file_ext, guess.extension), post_errors)
        file_ext = guess.extension
    return file_ext


def SaveImage(buffer, image, md5, image_file_ext, illust_url, post_errors):
    try:
        CreateData(buffer, md5, image_file_ext)
    except Exception as e:
        CreatePostError('utility.downloader.SaveImage', "Error saving image to disk: %s" % repr(e), post_errors)
        return False
    if storage.HasPreview(image.width, image.height):
        error = CreatePreview(image, md5)
        if error is not None:
            post_errors.append(error)
    if storage.HasSample(image.width, image.height):
        error = CreateSample(image, md5)
        if error is not None:
            post_errors.append(error)
    return True


def SaveVideo(buffer, md5, file_ext):
    try:
        return CreateVideo(buffer, md5, file_ext)
    except Exception as e:
        return DB.local.CreateError('utility.downloader.SaveVideo', "Error saving video to disk: %s" % repr(e))


def SaveThumb(thumb_illust_url, md5, source, post_errors):
    buffer, file_ext = DownloadMedia(thumb_illust_url, source)
    if DB.local.IsError(buffer):
        post_errors.append(buffer)
        return
    image = LoadImage(buffer)
    if DB.local.IsError(image):
        post_errors.append(image)
        return
    downsample = storage.HasPreview(image.width, image.height)
    error = CreatePreview(image, md5, downsample)
    if error is not None:
        post_errors.append(error)
    downsample = storage.HasSample(image.width, image.height)
    error = CreateSample(image, md5, downsample)
    if error is not None:
        post_errors.append(error)


def CheckVideoDimensions(filepath, video_illust_url, post_errors):
    try:
        probe = ffmpeg.probe(filepath)
    except Exception as e:
        CreatePostError('utility.downloader.CheckVideoDimensions', "Error reading video metadata: %e" % e, post_errors)
        return video_illust_url.width, video_illust_url.height
    video_stream = next(filter(lambda x: x['codec_type'] == 'video', probe['streams']), None)
    if video_stream is None:
        CreatePostError('utility.downloader.CheckVideoDimensions', "No video streams found: %e" % video_illust_url.url, post_errors)
        return video_illust_url.width, video_illust_url.height
    if (video_illust_url.width and video_stream['width'] != video_illust_url.width) or (video_illust_url.height and video_stream['height'] != video_illust_url.height):
        CreatePostError('utility.downloader.CheckVideoDimensions', "Mismatching image dimensions: Reported - %d x %d, Actual - %d x %d" % (video_illust_url.width, video_illust_url.height, video_stream['width'], video_stream['height']), post_errors)
    return video_stream['width'], video_stream['height']


def CheckImageDimensions(image, image_illust_url, post_errors):
    if (image_illust_url.width and image.width != image_illust_url.width) or (image_illust_url.height and image.height != image_illust_url.height):
        error = DB.local.CreateError('utility.downloader.SaveImage', "Mismatching image dimensions: Reported - %d x %d, Actual - %d x %d" % (image_illust_url.width, image_illust_url.height, image.width, image.height))
        post_errors.append(error)
    return image.width, image.height


def CreateImagePost(image_illust_url, source):
    buffer, file_ext = DownloadMedia(image_illust_url, source)
    if DB.local.IsError(buffer):
        return [buffer]
    md5 = CheckExisting(buffer, image_illust_url)
    if DB.local.IsError(md5):
        return [md5]
    post_errors = []
    image_file_ext = CheckFiletype(buffer, file_ext, post_errors)
    image = LoadImage(buffer)
    if DB.local.IsError(image):
        return post_errors + [image]
    image_width, image_height = CheckImageDimensions(image, image_illust_url, post_errors)
    if not SaveImage(buffer, image, md5, image_file_ext, image_illust_url, post_errors):
        return post_errors
    post = DB.local.CreatePostAndAddIllustUrl(image_illust_url, image_width, image_height, image_file_ext, md5, len(buffer))
    if len(post_errors):
        post.errors.extend(post_errors)
        DB.local.SaveData()
    return post


def CreateVideoPost(video_illust_url, thumb_illust_url, source):
    buffer, file_ext = DownloadMedia(video_illust_url, source)
    if DB.local.IsError(buffer):
        return [buffer]
    md5 = CheckExisting(buffer, video_illust_url)
    if DB.local.IsError(md5):
        return [md5]
    post_errors = []
    video_file_ext = CheckFiletype(buffer, file_ext, post_errors)
    filepath = SaveVideo(buffer, md5, video_file_ext)
    if DB.local.IsError(filepath):
        return post_errors + [filepath]
    video_width, video_height = CheckVideoDimensions(filepath, video_illust_url, post_errors)
    SaveThumb(thumb_illust_url, md5, source, post_errors)
    post = DB.local.CreatePostAndAddIllustUrl(video_illust_url, video_width, video_height, video_file_ext, md5, len(buffer))
    if len(post_errors):
        post.errors.extend(post_errors)
        DB.local.SaveData()
    return post
