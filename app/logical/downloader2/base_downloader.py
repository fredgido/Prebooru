def ConvertVideoUpload(illust, upload, source):
    video_illust_url, thumb_illust_url = source.VideoIllustDownloadUrls(illust)
    if thumb_illust_url is None:
        CreateAndAppendError('logical.downloader.DownloadVideo', "Did not find thumbnail for video on illust #%d" % illust.id, upload)
    else:
        post = CreateVideoPost(video_illust_url, thumb_illust_url, source)
        RecordOutcome(post, upload)


def ConvertImageupload(illust_url, upload, source):
    post = CreateImagePost(illust_url, source)
    RecordOutcome(post, upload)


def RecordOutcome(post, upload):
    if isinstance(post, list):
        post_errors = post
        valid_errors = [error for error in post_errors if IsError(error)]
        if len(valid_errors) != len(post_errors):
            print("\aInvalid data returned in outcome:", [item for item in post_errors if not IsError(item)])
        ExtendErrors(upload, valid_errors)
        AddUploadFailure(upload)
    else:
        UploadAppendPost(upload, post)
        AddUploadSuccess(upload)

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
        return CreateError('utility.downloader.CreatePreview', "Error creating preview: %s" % repr(e))


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
        return CreateError('utility.downloader.CreateSample', "Error creating sample: %s" % repr(e))


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
        return CreateError('utility.downloader.SaveVideo', "Error saving video to disk: %s" % repr(e))


def CheckExisting(buffer, illust_url):
    md5 = GetBufferChecksum(buffer)
    post = GetPostByMD5(md5)
    if post is not None:
        PostAppendIllustUrl(post, illust_url)
        return CreateError('utility.downloader.CheckExisting', "Image already uploaded on post #%d" % post.id)
    return md5

def CreatePostError(module, message, post_errors):
    error = CreateError(module, message)
    post_errors.append(error)


def LoadImage(buffer):
    try:
        file_imgdata = BytesIO(buffer)
        image = Image.open(file_imgdata)
    except Exception as e:
        return CreateError('utility.downloader.LoadImage', "Error processing image data: %s" % repr(e))
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

def CheckImageDimensions(image, image_illust_url, post_errors):
    if (image_illust_url.width and image.width != image_illust_url.width) or (image_illust_url.height and image.height != image_illust_url.height):
        CreatePostError('utility.downloader.SaveImage', "Mismatching image dimensions: Reported - %d x %d, Actual - %d x %d" % (image_illust_url.width, image_illust_url.height, image.width, image.height), post_errors)
    return image.width, image.height


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
