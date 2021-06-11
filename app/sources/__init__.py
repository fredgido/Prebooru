from . import pixiv
from . import twitter

SOURCES = [pixiv, twitter]
DICT = {
    'PIXIV': pixiv,
    'PXIMG': pixiv,
    'TWITTER': twitter,
    'TWIMG': twitter,
    'TWVIDEO': twitter
}
