# APP/DATABASE/UPLOAD_DB.PY

# ## LOCAL IMPORTS
from .. import models, SESSION
from ..logical.utility import GetCurrentTime


# ## FUNCTIONS

def CreateUploadFromParameters(createparams):
    data = {
        'illust_url_id': createparams['illust_url_id'],
        'media_filepath': createparams['media_filepath'],
        'sample_filepath': createparams['sample_filepath'],
        'request_url': createparams['request_url'],
        'successes': 0,
        'failures': 0,
        'status': 'pending',
        'subscription_id': None,
        'created': GetCurrentTime(),
    }
    if createparams['illust_url_id']:
        data['type'] = 'file'
    elif createparams['request_url']:
        data['type'] = 'post'
    upload = models.Upload(**data)
    SESSION.add(upload)
    SESSION.commit()
    if upload.type == 'post' and len(createparams['image_urls']):
        AppendImageUrls(upload, createparams['image_urls'])
    return upload


def AppendImageUrls(upload, image_urls):
    append_urls = [models.UploadUrl(url=url) for url in image_urls]
    SESSION.add_all(append_urls)
    SESSION.commit()
    upload.image_urls.extend(append_urls)
    SESSION.add(upload)
    SESSION.commit()
