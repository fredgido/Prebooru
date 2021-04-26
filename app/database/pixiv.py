# APP/DATABASE/PIXIV.PY


# ##PYTHON IMPORTS
import urllib
import datetime


# ##LOCAL IMPORTS
from .. import session as SESSION
from ..models import ArtistUrl, Artist, Tag, IllustUrl, PixivData, Illust
from ..logical.utility import ProcessTimestamp, GetCurrentTime
from ..sites import Site, GetSiteId, GetSiteDomain


# ##GLOBAL VARIABLES


# ##FUNCTIONS


def ProcessUTCTimestring(time_string):
    return datetime.datetime.utcfromtimestamp(ProcessTimestamp(time_string))


def UpdateRequery(instance, commit=True):
    instance.requery = GetCurrentTime() + datetime.timedelta(days=1)
    if commit:
        SESSION.add(instance)
        SESSION.commit()
    return instance


def ProcessIllustData(pixiv_data):
    artist = Artist.query.filter_by(site_id=Site.PIXIV.value, site_artist_id=int(pixiv_data['userId'])).first()
    if artist is None:
        artist = CreateArtistFromIllust(pixiv_data)
    illust = CreateIllustFromIllust(pixiv_data, artist.id)
    return illust


def CreateIllustFromIllust(pixiv_data, artist_id, commit=True):
    current_time = GetCurrentTime()
    data = {
        'site_id': Site.PIXIV.value,
        'site_illust_id': int(pixiv_data['illustId']),
        'site_created': ProcessUTCTimestring(pixiv_data['createDate']),
        'artist_id': artist_id,
        'description': pixiv_data['extraData']['meta']['twitter']['description'],
        'pages': pixiv_data['pageCount'],
        'score': pixiv_data['likeCount'],
        'requery': None,
        'created': current_time,
        'updated': current_time,
    }
    illust = Illust(**data)
    if commit:
        SESSION.add(illust)
        SESSION.commit()
        CreateIllustUrlFromIllust(pixiv_data, illust.id)
        AddIllustTags(illust, pixiv_data)
    return illust


def AddSiteData(illust, pixiv_data):
    sub_data = pixiv_data['userIllusts'][pixiv_data['illustId']]
    data = {
        'illust_id': illust.id,
        'site_uploaded': ProcessUTCTimestring(pixiv_data['uploadDate']),
        'site_updated': ProcessUTCTimestring(sub_data['updateDate']),
        'title': pixiv_data['title'],
        'bookmarks': pixiv_data['bookmarkCount'],
        'replies': pixiv_data['responseCount'],
        'views': pixiv_data['viewCount'],
    }
    site_data = PixivData(**data)
    SESSION.add(site_data)
    SESSION.commit()


def AddIllustTags(illust, pixiv_data):
    tags = GetDBTags(pixiv_data)
    if len(tags):
        illust.tags.extend(tags)
        SESSION.add(illust)
        SESSION.commit()


def GetDBTags(pixiv_data):
    def FindOrCommitTag(name):
        tag = Tag.query.filter_by(name=name).first()
        if tag is None:
            tag = Tag(name=name)
            SESSION.add(tag)
        return tag
    tags = []
    for tag_data in pixiv_data['tags']['tags']:
        tags.append(FindOrCommitTag(tag_data['tag']))
    if pixiv_data['isOriginal']:
        tags.append(FindOrCommitTag('original'))
    if len(tags):
        SESSION.commit()
    return tags


def CreateIllustUrlFromIllust(pixiv_data, illust_id, commit=True):
    parse = urllib.parse.urlparse(pixiv_data['urls']['original'])
    site_id = GetSiteId(parse.netloc)
    url = parse.path if site_id != 0 else pixiv_data['urls']['original']
    data = {
        'site_id': site_id,
        'url': url,
        'width': pixiv_data['width'],
        'height': pixiv_data['height'],
        'illust_id': illust_id,
        'order': 0,
        'active': True,
    }
    illust_url = IllustUrl(**data)
    if commit:
        SESSION.add(illust_url)
        SESSION.commit()
    return illust_url


def GetFullUrl(illust_url):
    return illust_url.url if illust_url.site_id == 0 else 'https://' + GetSiteDomain(illust_url.site_id) + illust_url.url


def CreateWebpagesFromUser(pixiv_data, artist_id, commit=True):
    artist_urls = []
    new_urls = []
    webpages = set()
    if pixiv_data['webpage'] is not None:
        webpages.add(pixiv_data['webpage'])
    for site in pixiv_data['social']:
        webpages.add(pixiv_data['social'][site]['url'])
    for page in webpages:
        artist_url = ArtistUrl.query.filter_by(artist_id=artist_id, url=page).first()
        if artist_url is None:
            data = {
                'artist_id': artist_id,
                'url': page,
            }
            artist_url = ArtistUrl(**data)
            new_urls.append(artist_url)
        artist_urls.append(artist_url)
    if commit and len(new_urls):
        SESSION.add_all(new_urls)
    return artist_urls


def CreateArtistFromIllust(pixiv_data, commit=True):
    current_time = GetCurrentTime()
    data = {
        'site_id': Site.PIXIV.value,
        'site_artist_id': int(pixiv_data['userId']),
        'site_account': pixiv_data['userAccount'],
        'name': pixiv_data['userName'],
        'profile': "",
        'requery': None,
        'created': current_time,
        'updated': current_time,
    }
    artist = Artist(**data)
    if commit:
        SESSION.add(artist)
        SESSION.commit()
    return artist


def CreateArtistFromUser(pixiv_data, commit=True):
    current_time = GetCurrentTime()
    data = {
        'site_id': Site.PIXIV.value,
        'site_artist_id': int(pixiv_data['userId']),
        'site_account': None,
        'name': pixiv_data['name'],
        'profile': pixiv_data['name'],
        'requery': None,
        'created': current_time,
        'updated': current_time,
    }
    artist = Artist(**data)
    if commit:
        SESSION.add(artist)
        SESSION.commit()
        CreateWebpagesFromUser(pixiv_data, artist.id)
    return artist


#   Update


def UpdateIllustFromIllust(illust, pixiv_data):
    updated = False
    temp_illust = CreateIllustFromIllust(pixiv_data, illust.artist_id, False)
    for c in temp_illust.__table__.columns:
        if c.key in ['id', 'artist_id', 'requery', 'created', 'updated']:
            continue
        value = getattr(temp_illust, c.key)
        if value is None:
            continue
        setattr(illust, c.key, value)
    if SESSION.is_modified(illust):
        print("Found updated illust info:", illust.id)
        updated = True
    temp_url = CreateIllustUrlFromIllust(pixiv_data, illust.id, False)
    first_url = IllustUrl.query.filter_by(illust_id=illust.id, order=0, active=True).first()
    if temp_url.url != first_url.url:
        first_url.active = False
        SESSION.add(first_url)
        SESSION.add(temp_url)
        updated = True
    if updated:
        illust.updated = GetCurrentTime()
        SESSION.add(illust)
        SESSION.commit()
    else:
        print("Nothing modified.")


def UpdateIllustUrlsFromPages(pixiv_data, illust):
    for i in range(0, len(pixiv_data)):
        image = pixiv_data[i]
        parse = urllib.parse.urlparse(image['urls']['original'])
        site_id = GetSiteId(parse.netloc)
        url = parse.path if site_id != 0 else image['urls']['original']
        active_url = IllustUrl.query.filter_by(illust_id=illust.id, order=i, active=True).first()
        if active_url is not None:
            if active_url.url == url:
                print("Found exisiting image URL:", active_url)
                continue
            active_url.active = False
            SESSION.add(active_url)
        data = {
            'site_id': site_id,
            'url': url,
            'width': image['width'],
            'height': image['height'],
            'illust_id': illust.id,
            'order': i,
            'active': True,
        }
        image_url = IllustUrl(**data)
        SESSION.add(image_url)
    UpdateRequery(illust, False)
    SESSION.add(illust)
    SESSION.commit()


def UpdateArtistFromUser(artist, pixiv_data):
    temp_artist = CreateArtistFromUser(pixiv_data, False)
    for c in temp_artist.__table__.columns:
        if c.key in ['id', 'artist_id', 'requery', 'created', 'updated']:
            continue
        value = getattr(temp_artist, c.key)
        if value is None:
            continue
        setattr(artist, c.key, value)
    if SESSION.is_modified(artist):
        print("Found updated artist info:", artist.id)
        artist.updated = GetCurrentTime()
    current_webpages = ArtistUrl.query.filter_by(artist_id=artist.id).all()
    active_webpages = CreateWebpagesFromUser(pixiv_data, artist.id, False)
    active_urls = [webpage.url for webpage in active_webpages]
    for webpage in active_webpages:
        if webpage.id is not None or webpage.active:
            continue
        if not webpage.active:
            print("Activated webpage:", webpage.url)
            webpage.active = True
        else:
            print("New webpage:", webpage.url)
        SESSION.add(webpage)
    for webpage in current_webpages:
        if webpage.url not in active_urls:
            print("Deactivated webpage:", webpage.url)
            webpage.active = False
            SESSION.add(webpage)
    UpdateRequery(artist, False)
    SESSION.add(artist)
    SESSION.commit()
