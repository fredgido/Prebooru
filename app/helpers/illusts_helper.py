from ..sites import GetSiteDomain, GetSiteKey
from ..sources import DICT as SOURCEDICT
from .base_helper import SearchUrlFor

def SiteDataIterator(illust):
    site_data_json = illust.site_data.to_json()
    for key,val in site_data_json.items():
        if key not in ['id', 'type', 'illust_id']:
            yield key, val


def OriginalUrl(illust_url):
    return 'https://' + GetSiteDomain(illust_url.site_id) + illust_url.url


def ShortLink(illust):
    site_key = GetSiteKey(illust.site_id)
    return "%s #%d" % (site_key.lower(), illust.site_illust_id)

def SiteIllustUrl(illust):
    site_key = GetSiteKey(illust.site_id)
    source = SOURCEDICT[site_key]
    return source.GetIllustUrl(illust.site_illust_id)


def PostSearch(illust):
    return SearchUrlFor('post.index_html', site_illust_id=illust.site_illust_id, isite_id=illust.site_id)

