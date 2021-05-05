# APP/SOURCES/TWITTER.PY

# ##PYTHON IMPORTS
import re
import time
import urllib
import requests

# ##LOCAL IMPORTS
from ..logical.utility import GetCurrentTime, GetFileExtension, GetHTTPFilename, SafeGet
from ..logical.downloader import DownloadMultipleImages, DownloadSingleImage
from ..logical.file import LoadDefault, PutGetJSON
from .. import database as DB
from ..config import workingdirectory, datafilepath
from ..sites import GetSiteDomain


# ##NOTES

"""
https://twitter.com/i/api/2/timeline/conversation/1381019619528347649.json
include_profile_interstitial_type: 1
include_blocking: 1
include_blocked_by: 1
include_followed_by: 1
include_want_retweets: 1
include_mute_edge: 1
include_can_dm: 1
include_can_media_tag: 1
skip_status: 1
cards_platform: Web-12
include_cards: 1
include_ext_alt_text: true
include_quote_count: true
include_reply_count: 1
tweet_mode: extended
include_entities: true
include_user_entities: true
include_ext_media_color: true
include_ext_media_availability: true
send_error_codes: true
simple_quoted_tweet: true
count: 20
include_ext_has_birdwatch_notes: false
ext: mediaStats,highlightedLabel
"""


# ###GLOBAL VARIABLES

#  Module variables

IMAGE_HEADERS = {}

#   Network


DATE_REGEX = re.compile(r""" ^
([\d]{4}-[\d]{2}-[\d]{2})?          # Date1
(?:\.\.)?                           # Non-capturing group for ..
(?(1)(?<=\.\.))                     # If Date1 exists, ensure .. exists
([\d]{4}-[\d]{2}-[\d]{2})?$         # Date2
""", re.X)

FILE_ID_REGEX = re.compile(r""" ^
(\d+)--                             # ID
(img(\d)--)?                        # Order
([\w-]+)                            # Filename
\.(jpg|png|gif|mp4)                 # Extension
""", re.X)

TWITPIC_REGEX = re.compile(r"""(
https?://                           # Schema
twitpic\.com                        # Domain
/(\w+)                              # Path
)""", re.X)

REQUEST_METHODS = {
    'GET': requests.get,
    'POST': requests.post
}

TWITTER_GUEST_AUTH = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

TWITTER_SIZES = [':orig', ':large', ':medium', ':small']

TWITTER_BASE_PARAMS = {
    "include_profile_interstitial_type": "1",
    "include_blocking": "1",
    "include_blocked_by": "1",
    "include_followed_by": "1",
    "include_want_retweets": "1",
    "include_mute_edge": "1",
    "include_can_dm": "1",
    "include_can_media_tag": "1",
    "skip_status": "1",
    "cards_platform": "Web-12",
    "include_cards": "1",
    "include_ext_alt_text": "true",
    "include_reply_count": "1",
    "tweet_mode": "extended",
    "include_entities": "true",
    "include_user_entities": "true",
    "include_ext_media_color": "true",
    "include_ext_media_availability": "true",
    "send_error_codes": "true",
    "simple_quoted_tweet": "true",
    "count": "20",
    "ext": "mediaStats,highlightedLabel,cameraMoment",
    "include_quote_count": "true"
}

TWITTER_SEARCH_PARAMS = {
    "tweet_search_mode": "live",
    "query_source": "typed_query",
    "pc": "1",
    "spelling_corrections": "1",
}

TOKEN_FILE = workingdirectory + datafilepath + 'twittertoken.txt'

#   Regexes

TWEET_RG = re.compile(r"""
^https?://twitter\.com                  # Hostname
/[\w-]+                                 # Account
/status
/(\d+)                                  # ID
(\?|$)                                  # End
""", re.X | re.IGNORECASE)

USERS_RG = re.compile(r"""
^https?://twitter\.com                  # Hostname
/([\w-]+)                               # Account
(\?|$)                                  # End
""", re.X | re.IGNORECASE)

"""https://pbs.twimg.com/media/Es5NR-YVgAQzpJP.jpg:orig"""
"""http://pbs.twimg.com/tweet_video_thumb/EiWHH0HVgAAbEcF.jpg"""

IMAGE1_RG = re.compile(r"""
^https?://pbs\.twimg\.com               # Hostname
/(media|tweet_video_thumb)
/([\w-]+)                               # Image key
\.(jpg|png|gif)                         # Extension
(?::(orig|large|medium|small|thumb))?   # Size
""", re.X | re.IGNORECASE)

"""https://pbs.twimg.com/media/Es5NR-YVgAQzpJP?format=jpg&name=900x900"""

IMAGE2_RG = re.compile(r"""
^https?://pbs\.twimg\.com               # Hostname
/(media|tweet_video_thumb)
/([\w-]+)                               # Image key
\?format=(jpg|png|gif)                  # Extension
(?:&name=(\w+))?$                       # Size
""", re.X | re.IGNORECASE)


"""http://pbs.twimg.com/ext_tw_video_thumb/1270031579470061568/pu/img/cLxRLtYjq_D10ome.jpg"""
""""https://pbs.twimg.com/amplify_video_thumb/1096312943845593088/img/VE7v_9MVr3tqZMNH.jpg"""

IMAGE3_RG = re.compile(r"""
^https?://pbs\.twimg\.com                   # Hostname
/(ext_tw_video_thumb|amplify_video_thumb)   # Type
/(\d+)                                      # Twitter ID
(?:/\w+)?
/img
/([^.?]+)                                   # Image key
\.(jpg|png|gif)                             # Extension
""", re.X | re.IGNORECASE)


"""https://video.twimg.com/tweet_video/EiWHH0HVgAAbEcF.mp4"""

VIDEO1_RG = re.compile(r"""
https?://video\.twimg\.com              # Hostname
/tweet_video
/(\w+)                                  # Video key
\.(mp4)                                 # Extension
""", re.X | re.IGNORECASE)


"""https://video.twimg.com/ext_tw_video/1270031579470061568/pu/vid/640x640/M54mOuT519Rb5eXs.mp4"""
"""https://video.twimg.com/amplify_video/1296680886113456134/vid/1136x640/7_ps073yayavGQUe.mp4"""

VIDEO2_RG = re.compile(r"""
https?://video\.twimg\.com              # Hostname
/(ext_tw_video|amplify_video)           # Type
/(\d+)                                  # Twitter ID
(?:/\w+)?
/vid
/(\d+)x(\d+)                            # Dimensions
/([^.?]+)                               # Video key
\.(mp4)                                 # Extension
""", re.X | re.IGNORECASE)


TWITTER_BASE_PARAMS = {
    "include_profile_interstitial_type": "1",
    "include_blocking": "1",
    "include_blocked_by": "1",
    "include_followed_by": "1",
    "include_want_retweets": "1",
    "include_mute_edge": "1",
    "include_can_dm": "1",
    "include_can_media_tag": "1",
    "skip_status": "1",
    "cards_platform": "Web-12",
    "include_cards": "1",
    "include_ext_alt_text": "true",
    "include_quote_count": "true",
    "include_reply_count": "1",
    "tweet_mode": "extended",
    "include_entities": "true",
    "include_user_entities": "true",
    "include_ext_media_color": "true",
    "include_ext_media_availability": "true",
    "send_error_codes": "true",
    "simple_quoted_tweet": "true",
    "include_ext_has_birdwatch_notes": "false",
    "ext": "mediaStats,highlightedLabel",
    "count": "20",
}

# ##FUNCTIONS

#   AUXILIARY


def LoadGuestToken():
    try:
        data = LoadDefault(TOKEN_FILE, {"token": None})
        return data['token']
    except Exception:
        return {"token": None}


def SaveGuestToken(guest_token):
    PutGetJSON(TOKEN_FILE, 'w', {"token": guest_token})

# Illust

IMAGE_URL_MAPPER = lambda x: IsImageUrl(GetFullUrl(x))
VIDEO_URL_MAPPER = lambda x: IsVideoUrl(GetFullUrl(x))

def IllustHasImages(illust):
    return any(map(IMAGE_URL_MAPPER, illust.urls))

def IllustHasVideos(illust):
    return any(map(VIDEO_URL_MAPPER, illust.urls))

def ImageIllustDownloadUrls(illust):
    return list(filter(lambda x: IMAGE_URL_MAPPER, illust.urls))

def VideoIllustDownloadUrls(illust):
    video_illust_url = next(filter(VIDEO_URL_MAPPER, illust.urls))
    thumb_illust_url = next(filter(IMAGE_URL_MAPPER, illust.urls), None)
    return video_illust_url, thumb_illust_url

#   URL

def GetMediaExtension(media_url):
    match = IMAGE1_RG.match(media_url) or IMAGE2_RG.match(media_url)
    if match:
        return match.group(3)
    match = VIDEO1_RG.match(media_url)
    if match:
        return match.group(2)
    match = VIDEO2_RG.match(media_url)
    if match:
        return match.group(6)
    filename = GetHTTPFilename(media_url)
    return GetFileExtension(filename)


def IsPostUrl(url):
    return bool(TWEET_RG.match(url))


def IsMediaUrl(url):
    return IsImageUrl(url) or IsVideoUrl(url)


def IsImageUrl(url):
    return bool(IMAGE1_RG.match(url) or IMAGE2_RG.match(url) or IMAGE3_RG.match(url))


def IsVideoUrl(url):
    return bool(VIDEO1_RG.match(url) or VIDEO2_RG.match(url))


def UploadCheck(request_url, referrer_url):
    return IsPostUrl(request_url) or (IsPostUrl(referrer_url) and IsMediaUrl(request_url))


def GetUploadType(request_url):
    # Have already validated urls with UploadCheck
    return 'post' if IsPostUrl(request_url) else 'image'


def GetIllustId(request_url, referrer_url):
    return int((TWEET_RG.match(request_url) or TWEET_RG.match(referrer_url)).group(1))


def GetFullUrl(illust_url):
    media_url = illust_url.url if illust_url.site_id == 0 else 'https://' + GetSiteDomain(illust_url.site_id) + illust_url.url
    if IMAGE1_RG.match(media_url):
        return media_url + ':orig'
    if IMAGE2_RG.match(media_url):
        return media_url + '&name=orig'
    return media_url


def GetIllustUrl(site_illust_id):
    return "https://twitter.com/i/web/status/%d" % site_illust_id

def SubscriptionCheck(request_url):
    artist_id = None
    artwork_match = USERS_RG.match(request_url)
    if artwork_match:
        artist_id = int(artwork_match.group(1))
    return artist_id


def NormalizeImageURL(image_url):
    image_match = IMAGE1_RG.match(image_url) or IMAGE2_RG.match(image_url)
    return r'/media/%s.%s' % (image_match.group(2), image_match.group(3))


def GetGlobalObjects(data, type_name):
    return SafeGet(data, 'globalObjects', type_name)


def GetGlobalObject(data, type_name, key):
    return SafeGet(data, 'globalObjects', type_name, key)


#   Database

def GetDBIllust(site_illust_id):
    print("GetDBIllust")
    error = None
    illust = DB.twitter.GetIllust(site_illust_id)
    if illust is None or illust.requery is None or illust.requery < GetCurrentTime():
        twitter_data = GetTwitterIllustTimeline(site_illust_id)
        if DB.local.IsError(twitter_data):
            print("Found error!")
            if illust is not None:
                DB.twitter.UpdateRequery(illust)
            return illust, twitter_data
        print("Getting tweet,user!")
        tweet = GetGlobalObject(twitter_data, 'tweets', str(site_illust_id))
        user = GetGlobalObject(twitter_data, 'users', tweet['user_id_str'])
        if illust is None:
            illust = DB.twitter.ProcessIllustData(tweet, user)
        else:
            artist = DB.twitter.GetArtist(illust.artist_id)
            DB.twitter.UpdateArtistFromUser(artist, user)
    else:
        print("Found illust #", illust.id)
    return illust, error


def GetDBArtist(illust):
    print("GetDBArtist")
    # The full user record is always given when querying the illust, so no need to requery here
    return DB.twitter.GetArtist(illust.artist_id), None


#   Network

def CheckGuestAuth(func):
    def wrapper(*args, **kwargs):
        if 'twitter_headers' not in globals() or twitter_headers is None:
            AuthenticateGuest()
        return func(*args, **kwargs)
    return wrapper


def AuthenticateGuest(override=False):
    global twitter_headers
    twitter_headers = {
        'authorization': 'Bearer %s' % TWITTER_GUEST_AUTH
    }
    guest_token = LoadGuestToken() if not override else None
    if guest_token is None:
        print("Authenticating as guest...")
        data = TwitterRequest('https://api.twitter.com/1.1/guest/activate.json', 'POST')
        print(data)
        guest_token = data['body']['guest_token']
        SaveGuestToken(guest_token)
    else:
        print("Loaded guest token from file.")
    twitter_headers['x-guest-token'] = guest_token


@CheckGuestAuth
def TwitterRequest(url, method='GET'):
    for i in range(3):
        try:
            response = REQUEST_METHODS[method](url, headers=twitter_headers, timeout=10)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            if i == 2:
                print("Connection errors exceeded!")
                return {'error': True, 'message': repr(e)}
            print("Pausing for network timeout...")
            time.sleep(5)
            continue
        if response.status_code == 200:
            break
        if response.status_code == 401:
            print(response.json())
            input()
        if response.status_code == 403 and SafeGet(response.json(), 'errors', 0, 'code') in [200, 239]:
            AuthenticateGuest(True)
        else:
            print("\n%s\nHTTP %d: %s (%s)" % (url, response.status_code, response.reason, response.text))
            return {'error': True, 'message': "HTTP %d - %s" % (response.status_code, response.reason)}
    try:
        data = response.json()
    except Exception:
        return {'error': True, 'message': "Error decoding response into JSON."}
    return {'error': False, 'body': data}


def GetTwitterIllustTimeline(illust_id):
    print("Getting twitter #%d" % illust_id)
    params = TWITTER_BASE_PARAMS.copy()
    url_params = urllib.parse.urlencode(params)
    data = TwitterRequest(("https://twitter.com/i/api/2/timeline/conversation/%d.json?" % illust_id) + url_params)
    if data['error']:
        return DB.local.CreateError('sources.twitter.GetTwitterIllust', data['message'])
    return data['body']
    tweet = GetGlobalObject(data['body'], 'tweets', str(illust_id))
    if tweet is None:
        return DB.local.CreateError('sources.twitter.GetTwitterIllust', "Tweet not found: %d" % illust_id)
    return data['body']


def GetTwitterIllust(illust_id):
    print("Getting twitter #%d" % illust_id)
    data = TwitterRequest('https://api.twitter.com/1.1/statuses/lookup.json?id=%d' % illust_id)
    if data['error']:
        return DB.local.CreateError('sources.twitter.GetTwitterIllust', data['message'])
    if len(data['body']) == 0:
        return DB.local.CreateError('sources.twitter.GetTwitterIllust', "Tweet not found: %d" % illust_id)
    return data['body'][0]


def GetTwitterArtist(artist_id):
    print("Getting user #%d" % artist_id)
    data = TwitterRequest('https://api.twitter.com/1.1/users/lookup.json?id=%s' % artist_id)
    if data['error']:
        return DB.local.CreateError('sources.twitter.GetTwitterArtist', data['message'])
    if len(data['body']) == 0:
        return DB.local.CreateError('sources.twitter.GetTwitterArtist', "User not found: %d" % artist_id)
    return data['body'][0]


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
