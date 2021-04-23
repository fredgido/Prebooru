# APP/SOURCES/PIXIV.PY

# ##PYTHON IMPORTS
import re
import time
import urllib
import requests
import threading
import datetime

# ##LOCAL IMPORTS
from ..logical.utility import GetCurrentTime, GetFileExtension, GetHTTPFilename
from ..logical.downloader import DownloadMultipleImages, DownloadSingleImage
from .. import database as DB
from ..config import PIXIV_PHPSESSID, SYSTEM_USER_ID
from ..sites import Site, GetSiteId

# ###GLOBAL VARIABLES

#   Network

API_HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-US,en;q=0.9',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) Waterfox/56.2'
}

API_JAR = requests.cookies.RequestsCookieJar()
API_JAR.set('PHPSESSID', PIXIV_PHPSESSID, domain='.pixiv.net', path='/', expires=None)

IMAGE_HEADERS = {
    'Referer': 'https://app-api.pixiv.net/'
}

IMAGE_SERVER = 'https://i.pximg.net'

#   Regexes

ARTWORKS_RG = re.compile(r"""
^https?://www\.pixiv\.net               # Hostname
/(?:en/)?artworks/                      # Path
(\d+)$                                  # ID
""", re.X | re.IGNORECASE)

USERS_RG = re.compile(r"""
^https?://www\.pixiv\.net               # Hostname
/(?:en/)?users/                         # Path
(\d+)$                                  # ID
""", re.X | re.IGNORECASE)

IMAGE_RG = re.compile(r"""
^https?://[^.]+\.pximg\.net             # Hostname
(?:/c/\w+)?                             # Size 1
/img-(?:original|master)/img/           # Path
\d{4}/\d{2}/\d{2}/\d{2}/\d{2}/\d{2}/    # Date
(\d+)_                                  # ID
p(\d+)                                  # Order
(?:_(?:master|square)1200)?             # Size 2
\.(jpg|png|gif|mp4|zip)                 # Extension
""", re.X | re.IGNORECASE)

PIXIV_FILE_REGEX = re.compile(r""" ^
(\d+)_                                  # ID
p(\d+)                                  # Order
\.(jpg|png|gif|mp4|zip)                 # Extension
""", re.X)

#   Other

ONE_DAY = 60 * 60 * 24

SITE_ID = 0
IMAGE_SITE_ID = 1

# ##FUNCTIONS

#   AUXILIARY


def GetDataIllustIDs(pixiv_data, type):
    try:
        return list(map(int, pixiv_data[type].keys()))
    except Exception:
        return []


#   URL

def GetImageExtension(image_url):
    filename = GetHTTPFilename(image_url)
    return GetFileExtension(filename)


def UploadCheck(request_url, referrer_url):
    return ARTWORKS_RG.match(request_url) or IMAGE_RG.match(request_url)


def GetUploadType(request_url, referrer_url):
    artwork_match = ARTWORKS_RG.match(request_url)
    if artwork_match:
        return 'post'
    if image_match:
        return 'image'

def GetIllustId(request_url, referrer_url):
    artwork_match = ARTWORKS_RG.match(request_url)
    if artwork_match:
        return int(artwork_match.group(1))
    if image_match:
        return int(image_match.group(1))

def GetUploadInfo(request_url):
    artwork_match = ARTWORKS_RG.match(request_url)
    if artwork_match:
        illust_id = int(artwork_match.group(1))
        type = 'post'
    image_match = IMAGE_RG.match(request_url) if artwork_match is None else None
    if image_match:
        illust_id = int(image_match.group(1))
        type = 'image'
    return type, illust_id


def SubscriptionCheck(request_url):
    artist_id = None
    artwork_match = USERS_RG.match(request_url)
    if artwork_match:
        artist_id = int(artwork_match.group(1))
    return artist_id


def NormalizeImageURL(image_url):
    image_url = urllib.parse.urlparse(image_url).path.replace('img-master', 'img-original')
    image_url = re.sub(r'_(?:master|square)1200', '', image_url)
    image_url = re.sub(r'(?:/c/\w+)', '', image_url)
    return image_url


def GetImageKey(filename):
    match = PIXIV_FILE_REGEX.match(filename)
    image_id = int(match.group(2))
    return image_id


#   Database


def GetDBIllust(pixiv_id):
    error = None
    illust = DB.models.Illust.query.filter_by(site_id=Site.PIXIV.value, site_illust_id=pixiv_id).first()
    if illust is None or illust.requery is None or illust.requery < GetCurrentTime():
        pixiv_data = GetPixivIllust(pixiv_id)
        if isinstance(pixiv_data, DB.models.Error):
            if illust is not None:
                DB.pixiv.UpdateRequery(illust)
            return illust, pixiv_data
        illust_id = int(pixiv_data['illustId'])
        if illust is None:
            illust = DB.pixiv.ProcessIllustData(pixiv_data)
        else:
            DB.pixiv.UpdateIllustFromIllust(illust, pixiv_data)
        if illust.pages > 1:
            error = UpdateWithPixivPageData(illust)
    else:
        print("Found illust #", illust.id)
    return illust, error


def GetDBArtist(illust):
    error = None
    artist = DB.models.Artist.query.filter_by(id=illust.artist_id).first()
    if artist.requery is None or artist.requery < GetCurrentTime():
        pixiv_data = GetPixivArtist(artist.site_artist_id)
        if isinstance(pixiv_data, DB.models.Error):
            DB.pixiv.UpdateRequery(artist)
            error = pixiv_data
        else:
            DB.pixiv.UpdateArtistFromUser(artist, pixiv_data)
    else:
        print("Found artist #", artist.id)
    return artist, error


def RequeryOrSaveArtist(artist):
    if artist['requery'] < time.time():
        threading.Thread(target=UpdateArtistDataFromArtist, args=(artist,)).start()
    else:
        threading.Thread(target=DB.pixiv.SaveDatabase).start()


#   Network


def PixivRequest(url):
    for i in range(3):
        try:
            response = requests.get(url, headers=API_HEADERS, cookies=API_JAR, timeout=10)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            if i ==2:
                print("Connection errors exceeded!")
                return {'error': True, 'message': repr(e)}
            print("Pausing for network timeout...")
            time.sleep(5)
            continue
        if response.status_code == 200:
            break
        print("\n%s\nHTTP %d: %s (%s)" % (url, response.status_code, response.reason, response.text))
        return {'error': True, 'message': "HTTP %d - %s" % (response.status_code, response.reason)}
    try:
        return response.json()
    except Exception:
        return {'error': True, 'message': "Error decoding response into JSON."}


def GetPixivIllust(illust_id):
    print("Getting pixiv #%d" % illust_id)
    data = PixivRequest("https://www.pixiv.net/ajax/illust/%d" % illust_id)
    if data['error']:
        return DB.local.CreateError('sources.pixiv.GetPixivIllust', data['message'])
    return data['body']


def GetPixivArtist(artist_id):
    print("Getting Pixiv user data...")
    data = PixivRequest("https://www.pixiv.net/ajax/user/%d?full=1" % artist_id)
    if data['error']:
        return DB.local.CreateError('sources.pixiv.GetPixivArtist', data['message'])
    return data['body']


def GetAllPixivArtistIllusts(artist_id):
    data = PixivRequest('https://www.pixiv.net/ajax/user/%d/profile/all' % artist_id)
    if data['error']:
        return DB.local.CreateError('sources.pixiv.GetAllPixivArtistIllusts', data['message'])
    ids = GetDataIllustIDs(data['body'], 'illusts')
    ids += GetDataIllustIDs(data['body'], 'manga')
    return ids


def GetPixivPageData(illust_id):
    print("Downloading pages for pixiv #%s" % illust_id)
    data = PixivRequest("https://www.pixiv.net/ajax/illust/%s/pages" % illust_id)
    if data['error']:
        return DB.local.CreateError('sources.pixiv.GetPixivPageData', data['message'])
    return data['body']


def UpdateWithPixivPageData(illust):
    error = None
    pixiv_data = GetPixivPageData(illust.site_illust_id)
    if isinstance(pixiv_data, DB.models.Error):
        DB.pixiv.UpdateRequery(illust)
        error = pixiv_data
    else:
        DB.pixiv.UpdateIllustUrlsFromPages(pixiv_data, illust)
    return error

"""
def UpdateArtistDataFromArtist(artist):
    pixiv_data = GetPixivArtist(artist.site_artist_id)
    if pixiv_data is not None:
        DB.pixiv.UpdateArtistFromUser(artist, pixiv_data)
    else:
        DB.pixiv.UpdateRequery(artist)
"""

#   Download


def DownloadIllust(pixiv_id, upload, type, module):
    illust = GetDBIllust(pixiv_id)
    if illust is None:
        print("Modify upload for bad illust!")
        return
    artist = GetDBArtist(illust)
    if artist is None:
        print("Modify upload for bad artist!")
        return
    return illust, artist

    if type == 'post' or type == 'subscription':
        DownloadMultipleImages(illust, upload, type, module)
    elif type == 'image':
        DownloadSingleImage(illust, upload, module)


def DownloadArtist(subscription, semaphore, module):
    pass
"""
    semaphore.acquire()
    print("Acquired semaphore for subscription:", subscription)
    #  Does this need a try/except/finally block to ensure semaphore release???
    artist_id = subscription['artist_id']
    illust_ids = GetAllPixivArtistIllusts(artist_id)
    if isinstance(illust_ids, str):
        subscription['errors'] = {
            'message': illust_ids,
            'time': round(time.time())
        }
        print("Releasing semaphore because of error:", illust_ids)
        semaphore.release()
        return
    existing_ids = [post['illust_id'] for post in DB.local.DATABASE['posts'] if post['artist_id'] == artist_id and post['site_id'] == SITE_ID]
    download_ids = list(set(illust_ids).difference(existing_ids))
    print("All:", illust_ids, "Existing:", existing_ids, "Download:", download_ids)
    for illust_id in download_ids:
        upload = DB.local.CreateUpload('subscription', SYSTEM_USER_ID, subscription_id=subscription['id'])
        DownloadIllust(illust_id, upload, 'subscription', module)
    artist = DB.pixiv.FindBy('artists', 'artist_id', illust_id)
    if artist is None and len(download_ids) == 0:
        # This should only happen for artists with no artworks
        pixiv_data = GetPixivArtist(artist_id)
        DB.pixiv.CreateArtistFromArtist(pixiv_data)
    subscription['requery'] = round(time.time()) + ONE_DAY
    DB.local.SaveDatabase()
    print("Releasing semaphore for subscription:", subscription)
    semaphore.release()
"""
