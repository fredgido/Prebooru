# APP/DATABASE/LOCAL.PY


# ##PYTHON IMPORTS
import time
import datetime

# ##LOCAL IMPORTS
from . import base
from ..logical.utility import GetCurrentTime
from ..config import workingdirectory, jsonfilepath
from . import models

# ##GLOBAL VARIABLES


DATABASE_FILE = workingdirectory + jsonfilepath + 'prebooru-local-data.json'

DATABASE_TABLES = ['posts', 'uploads', 'subscriptions']

DATABASE = None
ID_INDEXES = base.InitializeIDIndexes(DATABASE_TABLES)
OTHER_INDEXES = {
    'uploads': {},
    'posts': {
        'md5': {}
    },
    'subscriptions': {
        'artist_id': {}
    }
}
POST_MD5_INDEX = {}
SUBSCRIPTION_ARTIST_ID_INDEX = {}


# ##FUNCTIONS

#   I/O


def LoadDatabase():
    global DATABASE
    DATABASE = base.LoadDatabaseFile("LOCAL", DATABASE_FILE, DATABASE_TABLES, False)
    base.SetIndexes(ID_INDEXES, OTHER_INDEXES, DATABASE)


def SaveDatabase():
    base.SaveDatabaseFile("LOCAL", DATABASE, DATABASE_FILE, False)


#   Create


def CreateUpload(type, uploader_id, request_url=None, subscription_id=None):
    data = {
        'id': GetCurrentIndex('uploads') + 1,
        'uploader_id': uploader_id,
        'subscription_id': subscription_id,
        'request': request_url,
        'type': type,
        'post_ids': [],
        'successes': 0,
        'failures': 0,
        'errors': [],
        'created': round(time.time()),
    }
    base.CommitData(DATABASE, 'uploads', ID_INDEXES, OTHER_INDEXES, data)
    return data

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
    upload = models.Upload(**data)
    if commit:
        SESSION.add(upload)
        SESSION.commit()
        AppendUploadUrls(upload, image_urls)
    return upload

def AppendUploadUrls(upload, image_urls):
    append_urls = []
    for url in image_urls:
        append_urls.append(models.UploadUrl(url=url))
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
    post = models.Post(**data)
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



def CreateSubscription(artist_id, site_id, user_id):
    data = {
        'id': GetCurrentIndex('subscriptions') + 1,
        'artist_id': artist_id,
        'site_id': site_id,
        'user_id': user_id,
        'errors': None,
        'requery': 0
    }
    base.CommitData(DATABASE, 'subscriptions', ID_INDEXES, OTHER_INDEXES, data)
    return data

def CreateError(module_name, message, commit=True):
    data = {
        'module': module_name,
        'message': message,
        'created': GetCurrentTime(),
    }
    error = models.Error(**data)
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
    return models.Post.query.filter_by(**{field: value}).first()

#   Misc


def FindByID(table, id):
    return base.FindByID(ID_INDEXES, table, id)


def FindBy(table, key, value):
    return base.FindBy(OTHER_INDEXES, DATABASE, table, key, value)


def GetCurrentIndex(type):
    return base.GetCurrentIndex(DATABASE, type)

########################

def Initialize(db):
    global DB, SESSION
    DB = db
    SESSION = db.session

