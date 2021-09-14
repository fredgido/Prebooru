# APP/CACHE/MEDIA_FILE.PY

# ## LOCAL IMPORTS
import logging

from app import DB


# ## CLASSES

class MediaFile(DB.Model):
    # ## Declarations

    # #### SqlAlchemy

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    md5 = DB.Column(DB.String(255), nullable=False)
    file_ext = DB.Column(DB.String(255), nullable=False)
    media_url = DB.Column(DB.String(255), nullable=False)
    expires = DB.Column(DB.DateTime(timezone=False), nullable=False)

    # ## Property methods

    @property
    def file_url(self):
        logging.exception('MediaFile.file_url')
        return ''
        # return url_for('images.send_file', path=f'data/{self.md5[0:2]}/{self.md5[2:4]}/{self.md5}.{self.file_ext}')
        # return CacheNetworkUrlpath() + self.md5 + '.' + self.file_ext

    @property
    def file_path(self):
        logging.exception('MediaFile.file_url')
        return ''
