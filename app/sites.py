from enum import Enum, auto
from urllib.parse import urlparse

class Site(Enum):
    PIXIV = auto()
    PXIMG = auto()
    TWITTER = auto()
    TWIMG = auto()

"""
class AttrDict(object):
    def __init__(self, args):
        for k in args:
            setattr(self, k, args[k])
    def __getitem__(self, item):
        return getattr(self, item)
"""

SITES = {
    'PIXIV': 'www.pixiv.net',
    'PXIMG': 'i.pximg.net',
    'TWITTER': 'twitter.com',
    'TWIMG': 'pbs.twimg.com',
}

DOMAINS = {v: k for k, v in SITES.items()}

def GetSiteId(domain):
    if domain in DOMAINS:
        s = DOMAINS[domain]
        return Site[s].value
    return 0

def GetSiteDomain(site_id):
    return SITES[Site(site_id).name]