# APP/DATABASE/LOCAL.PY

# ##LOCAL IMPORTS
from ..logical.utility import GetCurrentTime
from .. import session as SESSION
from ..models import Error, Post, UploadUrl, Upload


# ##FUNCTIONS


def CreateUploadFromRequest(type, request_url, image_urls, uploader_id, commit=True):
    data = {
        'uploader_id': uploader_id,
        'request_url': request_url,
        'type': type,
        'status': 'pending',
        'successes': 0,
        'failures': 0,
        'subscription_id': None,
        'created': GetCurrentTime(),
    }
    upload = Upload(**data)
    if commit:
        SESSION.add(upload)
        SESSION.commit()
        AppendUploadUrls(upload, image_urls)
    return upload


def AppendUploadUrls(upload, image_urls):
    append_urls = []
    for url in image_urls:
        append_urls.append(UploadUrl(url=url))
    if len(append_urls):
        SESSION.add_all(append_urls)
        SESSION.commit()
        upload.image_urls.extend(append_urls)
        SESSION.add(upload)
        SESSION.commit()


def CreatePost(width, height, file_ext, md5, size, commit=True):
    data = {
        'width': width,
        'height': height,
        'file_ext': file_ext,
        'md5': md5,
        'size': size,
        'created': GetCurrentTime(),
    }
    post = Post(**data)
    if commit:
        SESSION.add(post)
        SESSION.commit()
    return post


def AppendPostIllustUrl(post, illust_url):
    post.illust_urls.append(illust_url)
    SESSION.add(post)
    SESSION.commit()


def CreatePostAndAddIllustUrl(illust_url, width, height, file_ext, md5, size):
    post = CreatePost(width, height, file_ext, md5, size)
    AppendPostIllustUrl(post, illust_url)
    return post


def CreateError(module_name, message, commit=True):
    data = {
        'module': module_name,
        'message': message,
        'created': GetCurrentTime(),
    }
    error = Error(**data)
    if commit:
        SESSION.add(error)
        SESSION.commit()
    return error


def AppendError(instance, error):
    instance.errors.append(error)
    SESSION.add(error)
    SESSION.commit()


def CreateAndAppendError(module_name, message, instance):
    error = CreateError(module_name, message)
    AppendError(instance, error)
    return error


def SaveData(instance):
    SESSION.add(instance)
    SESSION.commit()


def GetDBPostByField(field, value):
    return Post.query.filter_by(**{field: value}).first()


def IsError(instance):
    return isinstance(instance, Error)
