from .. import db
from ..storage import CACHE_DATA_DIRECTORY, CACHE_NETWORK_URLPATH

class MediaFile(db.Model):
    __bind_key__ = 'cache'
    id = db.Column(db.Integer, primary_key=True)
    md5 = db.Column(db.String(255), nullable=False)
    file_ext = db.Column(db.String(255), nullable=False)
    media_url = db.Column(db.String(255), nullable=False)
    expires = db.Column(db.DateTime(timezone=False), nullable=False)

    @property
    def file_url(self):
        return CACHE_NETWORK_URLPATH + self.md5 + '.' + self.file_ext

    @property
    def file_path(self):
        return CACHE_DATA_DIRECTORY + self.md5 + '.' + self.file_ext

