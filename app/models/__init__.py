# APP/MODELS/__INIT__.PY

# flake8: noqa

from .. import DB

# SITE DATA

from .tag import Tag
from .label import Label
from .description import Description
from .site_data import SiteData, PixivData, TwitterData
from .illust_url import IllustUrl
from .illust import Illust
from .artist_url import ArtistUrl
from .artist import Artist
from .booru import Booru

# LOCAL DATA

from .error import Error
from .post import Post
from .upload_url import UploadUrl
from .upload import Upload
from .notation import Notation
from .pool import Pool
from .pool_element import PoolElement, PoolPost, PoolIllust, PoolNotation
from .subscription import Subscription

# Set relationships that cannot be set at loading time
IllustUrl.uploads = DB.relationship(Upload, backref=DB.backref('illust_url', lazy=True), lazy=True)

NONCE = None
