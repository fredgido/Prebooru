# APP/SOURCES/TWITTER.PY

# ##PYTHON IMPORTS
import re
import time
import json
import urllib
import requests

# ##LOCAL IMPORTS
from ..logical.utility import GetCurrentTime, GetFileExtension, GetHTTPFilename, SafeGet
from ..logical.downloader import DownloadMultipleImages, DownloadSingleImage
from ..logical.file import LoadDefault, PutGetJSON
from ..logical.logger import LogError
from ..database import twitter as DB, local as DBLOCAL
from ..config import workingdirectory, datafilepath
from ..sites import GetSiteDomain, GetSiteId


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

DB = DB

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
/([^.]+)                               # Image key
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
"""https://pbs.twimg.com/amplify_video_thumb/1096312943845593088/img/VE7v_9MVr3tqZMNH.jpg"""

IMAGE3_RG = re.compile(r"""
^https?://pbs\.twimg\.com                   # Hostname
/(ext_tw_video_thumb|amplify_video_thumb)   # Type
/(\d+)                                      # Twitter ID
(/\w+)?                                     # Path
/img
/([^.]+)                                    # Image key
\.(jpg|png|gif)                             # Extension
(?::(orig|large|medium|small|thumb))?       # Size
""", re.X | re.IGNORECASE)


"""https://video.twimg.com/tweet_video/EiWHH0HVgAAbEcF.mp4"""

VIDEO1_RG = re.compile(r"""
https?://video\.twimg\.com              # Hostname
/tweet_video
/([^.]+)                                  # Video key
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
/([^.]+)                               # Video key
\.(mp4)                                 # Extension
""", re.X | re.IGNORECASE)


TWITTER_BASE_PARAMS = {
    "include_profile_interstitial_type": "false",
    "include_blocking": "false",
    "include_blocked_by": "false",
    "include_followed_by": "false",
    "include_want_retweets": "false",
    "include_mute_edge": "false",
    "include_can_dm": "false",
    "include_can_media_tag": "false",
    "skip_status": "true",
    #"cards_platform": "Web-12",
    "include_cards": "false",
    "include_ext_alt_text": "false",
    "include_quote_count": "true",
    "include_reply_count": "true",
    "tweet_mode": "extended",
    "include_entities": "true",
    "include_user_entities": "true",
    "include_ext_media_color": "false",
    "include_ext_media_availability": "false",
    "send_error_codes": "true",
    "simple_quoted_tweet": "true",
    "include_ext_has_birdwatch_notes": "false",
    "ext": "mediaStats",
    "count": "1",
}

ILLUST_SHORTLINK = 'twitter #%d'
ARTIST_SHORTLINK = 'twuser #%d'

ILLUST_HREFURL = 'https://twitter.com/i/web/status/%d'
#ARTIST_HREFURL = 'https://twitter.com/intent/user?user_id=%d'
ARTIST_HREFURL = 'https://twitter.com/i/user/%d'

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

def PostHasImages(post):
    return any(map(IMAGE_URL_MAPPER, post.illust_urls))

def PostHasVideos(post):
    return any(map(VIDEO_URL_MAPPER, post.illust_urls))

def ImageIllustDownloadUrls(illust):
    return list(filter(lambda x: IMAGE_URL_MAPPER, illust.urls))

def VideoIllustDownloadUrls(illust):
    video_illust_url = next(filter(VIDEO_URL_MAPPER, illust.urls))
    thumb_illust_url = next(filter(IMAGE_URL_MAPPER, illust.urls), None)
    return video_illust_url, thumb_illust_url

def VideoIllustVideoUrl(illust):
    return next(filter(VIDEO_URL_MAPPER, illust.urls), None)

def VideoIllustThumbUrl(illust):
    return next(filter(IMAGE_URL_MAPPER, illust.urls), None)

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
    return IsPostUrl(request_url) or (referrer_url and IsPostUrl(referrer_url) and IsMediaUrl(request_url))


def GetUploadType(request_url):
    # Have already validated urls with UploadCheck
    return 'post' if IsPostUrl(request_url) else 'image'


def SiteId():
    return GetSiteId('twitter.com')

def GetIllustId(request_url, referrer_url):
    return int((TWEET_RG.match(request_url) or TWEET_RG.match(referrer_url)).group(1))


def GetFullUrl(illust_url):
    media_url = GetMediaUrl(illust_url)
    if IMAGE1_RG.match(media_url):
        return media_url + ':orig'
    if IMAGE2_RG.match(media_url):
        return media_url + '&name=orig'
    return media_url

def SmallImageUrl(image_url):
    return NormalizedImageUrl(image_url) + ':small'

def NormalizedImageUrl(image_url):
    match = IMAGE1_RG.match(image_url) or IMAGE2_RG.match(image_url)
    if match:
        type, imagekey, extension, _ = match.groups()
        return "https://pbs.twimg.com/%s/%s.%s" % (type, imagekey, extension)
    match = IMAGE3_RG.match(image_url)
    type, imageid, path, imagekey, extension, _ = match.groups()
    path = path or ""
    return "https://pbs.twimg.com/%s/%s%s/img/%s.%s" % (type, imageid, path, imagekey, extension)

def GetMediaUrl(illust_url):
    return illust_url.url if illust_url.site_id == 0 else 'https://' + GetSiteDomain(illust_url.site_id) + illust_url.url

def GetPostUrl(illust):
    tweet_id = illust.site_illust_id
    screen_name = illust.artist.current_site_account
    if screen_name is None:
        return GetIllustUrl(tweet_id)
    else:
        return "https://twitter.com/%s/status/%d" % (screen_name, tweet_id)

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

def HasArtistUrls(artist):
    return (artist.current_site_account is not None) or (len(artist.site_accounts) == 1)

def ArtistMainUrl(artist):
    if not HasArtistUrls(artist):
        return ""
    screen_name = artist.current_site_account if artist.current_site_account is not None else artist.site_accounts[0].name
    return 'https://twitter.com/%s' % screen_name

def ArtistMediaUrl(artist):
    url = ArtistMainUrl(artist)
    return url + '/media' if len(url) else ""

def ArtistLikesUrl(artist):
    url = ArtistMainUrl(artist)
    return url + '/likes' if len(url) else ""

def GetGlobalObjects(data, type_name):
    return SafeGet(data, 'globalObjects', type_name)


def GetGlobalObject(data, type_name, key):
    return SafeGet(data, 'globalObjects', type_name, key)


#   Database

def Prework(site_illust_id):
    print("Prework")
    illust = DB.GetSiteIllust(site_illust_id)
    if illust is not None:
        return
    twitter_data = GetTwitterIllustTimeline(site_illust_id)
    if DBLOCAL.IsError(twitter_data):
        print("Found error!")
        return twitter_data
    print("Getting tweet,user!")
    tweets = GetGlobalObjects(twitter_data, 'tweets')
    DB.CacheTimelineData(tweets, 'illust')
    users = GetGlobalObjects(twitter_data, 'users')
    DB.CacheTimelineData(users, 'artist')

"""
    tweet = GetGlobalObject(twitter_data, 'tweets', str(site_illust_id))
    twuser = GetGlobalObject(twitter_data, 'users', tweet['user_id_str'])
    if tweet is None or twuser is None:
        return DBLOCAL.CreateError('sources.twitter.Prework', "Unable to parse tweet/user data: %d" % site_illust_id)
    artist = DB.GetSiteArtist(int(twuser['id_str']))
    if artist is None:
        artist = DB.CreateArtistFromUser(twuser)
    elif DBLOCAL.CheckRequery(artist):
        DB.UpdateArtistFromUser(artist, twuser)
    DB.CreateIllustFromTweet(tweet, artist.id)
"""


"""
def GetDBArtist(illust):
    print("GetDBArtist")
    # The full user record is always given when querying the illust, so no need to requery here
    return DB.GetArtist(illust.artist_id), None
"""

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
        #print(data)
        guest_token = data['body']['guest_token']
        SaveGuestToken(guest_token)
    else:
        print("Loaded guest token from file.")
    twitter_headers['x-guest-token'] = guest_token


@CheckGuestAuth
def TwitterRequest(url, method='GET'):
    reauthenticated = False
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
        #if response.status_code == 401:
            #print("HTTP 401:", url, response.text)
            #LogError('sources.twitter.TwitterRequest', "HTTP 401 on URL %s: %s" % (url, response.text))
            #raise Exception("Unhandled HTTP code!")
        if not reauthenticated and (response.status_code == 401 or (response.status_code == 403 and SafeGet(response.json(), 'errors', 0, 'code') in [200, 239])):
            AuthenticateGuest(True)
            reauthenticated = True
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
        return DBLOCAL.CreateError('sources.twitter.GetTwitterIllust', data['message'])
    return data['body']
    tweet = GetGlobalObject(data['body'], 'tweets', str(illust_id))
    if tweet is None:
        return DBLOCAL.CreateError('sources.twitter.GetTwitterIllust', "Tweet not found: %d" % illust_id)
    return data['body']


def GetTwitterIllust(illust_id):
    print("Getting twitter #%d" % illust_id)
    data = TwitterRequest('https://api.twitter.com/1.1/statuses/lookup.json?id=%d&trim_user=true&tweet_mode=extended&include_quote_count=true&include_reply_count=true' % illust_id)
    if data['error']:
        return DBLOCAL.CreateError('sources.twitter.GetTwitterIllust', data['message'])
    if len(data['body']) == 0:
        return DBLOCAL.CreateError('sources.twitter.GetTwitterIllust', "Tweet not found: %d" % illust_id)
    return data['body'][0]


"""
TwitterRequest('https://twitter.com/i/api/graphql/WN6Hck-Pwm-YP0uxVj1oMQ/UserByRestIdWithoutResults?%s' % urllib.parse.urlencode({'variables': json.dumps({'userId': '2267697692', 'withHighlightedLabel': False})}))
"""

def GetTwitterArtist(artist_id):
    print("Getting user #%d" % artist_id)
    jsondata = {
        'userId': str(artist_id),
        'withHighlightedLabel': False,
    }
    urladdons = urllib.parse.urlencode({'variables': json.dumps(jsondata)})
    data = TwitterRequest('https://twitter.com/i/api/graphql/WN6Hck-Pwm-YP0uxVj1oMQ/UserByRestIdWithoutResults?%s' % urladdons)
    if data['error']:
        return DBLOCAL.CreateError('sources.twitter.GetTwitterIllust', data['message'])
    twitterdata = data['body']
    if 'errors' in twitterdata and len(twitterdata['errors']):
        return DBLOCAL.CreateError('sources.twitter.GetTwitterArtist', '; '.join([error['message'] for error in twitterdata['errors']]))
    userdata = SafeGet(twitterdata, 'data', 'user')
    if userdata is None or 'rest_id' not in userdata or 'legacy' not in userdata:
        return DBLOCAL.CreateError('sources.twitter.GetTwitterArtist', "Error parsing data: %s" % json.dumps(twitterdata))
    retdata = userdata['legacy']
    retdata['id_str'] = userdata['rest_id']
    return retdata

#   Update

def UpdateArtist(artist, explicit=False):
    twuser = DB.GetApiArtist(artist.site_artist_id)
    if twuser is None:
        twuser = GetTwitterArtist(artist.site_artist_id)
        if DBLOCAL.IsError(twuser):
            print("Error getting artist data!")
            artist.active = False
            DBLOCAL.SaveData()
            return
        DB.CacheLookupData([twuser], 'artist')
    DB.UpdateArtistFromUser(artist, twuser)

def UpdateIllust(illust, explicit=False, timeline=False):
    tweet = DB.GetApiIllust(illust.site_illust_id)
    if tweet is None:
        tweet = GetTwitterIllust(illust.site_illust_id)
        if DBLOCAL.IsError(tweet):
            print("Error getting illust data!")
            illust.active = False
            DBLOCAL.SaveData()
            return
        DB.CacheLookupData([tweet], 'illust')
    DB.UpdateIllustFromTweet(illust, tweet)

# Create


def CreateArtist(site_artist_id):
    ### INCLUDED ONLY DURING TESTING PHASE ###
    artist = DB.GetSiteArtist(site_artist_id)
    if artist is not None:
        return artist
    ### ###
    twuser = DB.GetApiIllust(site_artist_id)
    if twuser is None:
        twuser = GetTwitterArtist(site_artist_id)
        if DBLOCAL.IsError(twuser):
            print("Error getting artist data!")
            # Shouldn't be anything else that can be done
            return twuser
    return DB.CreateArtistFromUser(twuser)


def CreateDBArtistFromParams(params):
    return DB.CreateArtistFromParameters(params)

def CreateDBIllustFromParams(params):
    return DB.CreateIllustFromParameters(params)

def CreateIllust(site_illust_id, timeline=False):
    ### INCLUDED ONLY DURING TESTING PHASE ###
    illust = DB.GetSiteIllust(site_illust_id)
    if illust is not None:
        return illust
    ### ###
    tweet = DB.GetApiIllust(site_illust_id)
    if tweet is None:
        tweet = GetTwitterIllust(site_illust_id)
        if DBLOCAL.IsError(tweet):
            print("Error getting artist data!")
            # Shouldn't be anything else that can be done
            return tweet
    if 'user' in tweet:
        twuser_id = tweet['user']['id']
    elif 'user_id_str' in tweet:
        twuser_id = int(tweet['user_id_str'])
    else:
        return DBLOCAL.CreateError('sources.twitter.CreateIllust', "Unknown API data structure on tweet #%d" % site_illust_id)
    artist = DB.GetSiteArtist(twuser_id)
    if artist is None:
        artist = CreateArtist(twuser_id)
        if DBLOCAL.IsError(artist):
            return artist
    return DB.CreateIllustFromTweet(tweet, artist.id)

#   Download

"""
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