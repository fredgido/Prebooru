# APP/CACHE/API_DATA.PY

# ##LOCAL IMPORTS
from .. import DB
from ..storage import CACHE_DATA_DIRECTORY, CACHE_NETWORK_URLPATH

# ##GLOBAL VARIABLES

class MediaFile(DB.Model):
    __bind_key__ = 'cache'
    id = DB.Column(DB.Integer, primary_key=True)
    md5 = DB.Column(DB.String(255), nullable=False)
    file_ext = DB.Column(DB.String(255), nullable=False)
    media_url = DB.Column(DB.String(255), nullable=False)
    expires = DB.Column(DB.DateTime(timezone=False), nullable=False)

    @property
    def file_url(self):
        return CACHE_NETWORK_URLPATH + self.md5 + '.' + self.file_ext

    @property
    def file_path(self):
        return CACHE_DATA_DIRECTORY + self.md5 + '.' + self.file_ext

