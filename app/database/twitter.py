# APP/DATABASE/TWITTER.PY

# ##PYTHON IMPORTS
import re
import urllib
import datetime


# ##LOCAL IMPORTS
from . import base as BASE
from .. import session as SESSION
from ..models import ArtistUrl, Artist, Tag, IllustUrl, TwitterData, Illust, Label, Description
from ..cache import ApiData
from ..logical.utility import GetCurrentTime, DaysFromNow, SafeGet
from ..sites import Site, GetSiteId


# ##GLOBAL VARIABLES


SHORT_URL_REPLACE_RG = re.compile(r"""
https?://t\.co                         # Hostname
/ [\w-]+                               # Account
""", re.X | re.IGNORECASE)


# ##FUNCTIONS


def ProcessTwitterTimestring(time_string):
    return datetime.datetime.strptime(time_string, '%a %b %d %H:%M:%S +0000 %Y')


###MOVE TO LOCAL
def UpdateRequery(instance, commit=True):
    instance.requery = GetCurrentTime() + datetime.timedelta(days=1)
    if commit:
        SESSION.commit()
    return instance

def UpdateTimestamps(instance, dirty):
    if dirty:
        instance.updated = GetCurrentTime()
    instance.requery = GetCurrentTime() + datetime.timedelta(days=1)
###ENDMOVE


def ProcessIllustData(tweet, user):
    print("ProcessIllustData")
    artist = Artist.query.filter_by(site_id=Site.TWITTER.value, site_artist_id=int(tweet['user_id_str'])).first()
    if artist is None:
        artist = CreateArtistFromUser(user)
    elif artist.requery is None or artist.requery < GetCurrentTime():
        # UpdateArtistFromUser(artist, user)
        pass
    illust = CreateIllustFromTweet(tweet, artist.id)
    return illust


def CreateIllustFromTweet(tweet, artist_id, commit=True):
    print("CreateIllustFromTweet")
    current_time = GetCurrentTime()
    data = {
        'site_id': Site.TWITTER.value,
        'site_illust_id': int(tweet['id_str']),
        'site_created': ProcessTwitterTimestring(tweet['created_at']),
        'artist_id': artist_id,
        'pages': len(tweet['extended_entities']['media']),
        'score': tweet['favorite_count'],
        'requery': GetCurrentTime() + datetime.timedelta(days=1),
        'created': current_time,
        'updated': current_time,
    }
    illust = Illust(**data)
    if commit:
        SESSION.add(illust)
        SESSION.commit()
        AddSiteData(illust, tweet)
        AddIllustDescription(illust, tweet)
        AddIllustTags(illust, tweet)
        AddIllustUrls(illust, tweet)
        AddVideoUrls(illust, tweet)
    return illust


def CreateIllustFromParameters(params):
    if 'site_created' in params:
        try:
            params['site_created'] = ProcessTwitterTimestring(params['site_created'])
        except Exception:
            del params['site_created']
    return BASE.CreateIllustFromParameters(params, Site.TWITTER.value)


def AddIllustDescription(illust, tweet):
    description_text = GetTweetText(tweet)
    current_descriptions = [descr.body for descr in illust.descriptions]
    if description_text in current_descriptions:
        return
    descr = Description.query.filter_by(body=description_text).first()
    if descr is None:
        descr = Description(body=description_text)
    illust.descriptions.append(descr)
    SESSION.add(illust)
    SESSION.commit()


def AddIllustTags(illust, tweet):
    print("AddIllustTags")
    tags = GetDBTags(tweet)
    if len(tags):
        illust.tags.extend(tags)
        SESSION.add(illust)
        SESSION.commit()


def AddSiteData(illust, tweet):
    print("AddSiteData")
    data = {
        'illust_id': illust.id,
        'retweets': tweet['retweet_count'],
        'replies': tweet['reply_count'] if 'reply_count' in tweet else None,
        'quotes': tweet['quote_count'] if 'quote_count' in tweet else None,
    }
    site_data = TwitterData(**data)
    SESSION.add(site_data)
    SESSION.commit()


def GetDBTags(tweet):
    print("GetDBTags")

    def FindOrCommitTag(name):
        tag = Tag.query.filter_by(name=name).first()
        if tag is None:
            tag = Tag(name=name)
            SESSION.add(tag)
            SESSION.commit()
        return tag

    tag_data = SafeGet(tweet, 'entities', 'hashtags') or []
    tags = []
    seen = set()
    for entry in tag_data:
        tagname = entry['text'].lower()
        if tagname in seen:
            continue
        tags.append(FindOrCommitTag(tagname))
        seen.add(tagname)
    if len(tags):
        SESSION.commit()
    return tags


def GetIllustUrlInfo(entry):
    from ..sources.twitter import IMAGE2_RG
    query_addon = ""
    if entry['type'] == 'photo':
        parse = urllib.parse.urlparse(entry['media_url_https'])
        dimensions = (entry['original_info']['width'], entry['original_info']['height'])
        match = IMAGE2_RG.match(entry['media_url_https'])
        if match:
            query_addon = '?format=%s' % match.group(3)
    elif entry['type'] == 'video' or entry['type'] == 'animated_gif':
        variants = entry['video_info']['variants']
        valid_variants = [variant for variant in variants if 'bitrate' in variant]
        max_bitrate = max(map(lambda x: x['bitrate'], valid_variants))
        max_video = next(filter(lambda x: x['bitrate'] == max_bitrate, valid_variants))
        parse = urllib.parse.urlparse(max_video['url'])
        dimensions = (entry['sizes']['large']['w'], entry['sizes']['large']['h'])
    else:
        return None, None, None
    site_id = GetSiteId(parse.netloc)
    url = parse.path + query_addon if site_id != 0 else parse.geturl()
    return url, site_id, dimensions


def AddIllustUrls(illust, tweet, commit=True):
    print("AddIllustUrls")
    url_data = SafeGet(tweet, 'entities', 'media') or []
    illust_urls = []
    for i in range(0, len(url_data)):
        url, site_id, dimensions = GetIllustUrlInfo(url_data[i])
        if url is None:
            continue
        data = {
            'site_id': site_id,
            'url': url,
            'width': dimensions[0],
            'height': dimensions[1],
            'illust_id': illust.id,
            'order': i,
            'active': True,
        }
        illust_url = IllustUrl(**data)
        illust_urls.append(illust_url)
    if commit and len(illust_urls) > 0:
        SESSION.add_all(illust_urls)
        SESSION.commit()
    return illust_urls


def AddVideoUrls(illust, tweet, commit=True):
    print("AddVideoUrls")
    url_data = SafeGet(tweet, 'extended_entities', 'media') or []
    video_url_data = [url_entry for url_entry in url_data if url_entry['type'] in ['animated_gif', 'video']]
    if len(video_url_data) == 0:
        return []
    url, site_id, dimensions = GetIllustUrlInfo(video_url_data[0])
    print("Video url info", url, site_id, dimensions)
    if url is None:
        return []
    data = {
        'site_id': site_id,
        'url': url,
        'width': dimensions[0],
        'height': dimensions[1],
        'illust_id': illust.id,
        'order': 0,
        'active': True,
    }
    video_url = IllustUrl(**data)
    if commit:
        SESSION.add(video_url)
        SESSION.commit()
    return video_url


def AddArtistName(artist, name_text):
    print("AddArtistName")
    current_names = [label.name for label in artist.names]
    if name_text in current_names:
        return False
    lbl = Label.query.filter_by(name=name_text).first()
    if lbl is None:
        lbl = Label(name=name_text)
    artist.names.append(lbl)
    SESSION.commit()
    print("Added artist name:", name_text)
    return True


def AddArtistSiteAccount(artist, site_account_text):
    print("AddArtistSiteAccount")
    current_site_accounts = [label.name for label in artist.site_accounts]
    if site_account_text in current_site_accounts:
        return False
    lbl = Label.query.filter_by(name=site_account_text).first()
    if lbl is None:
        lbl = Label(name=site_account_text)
    artist.site_accounts.append(lbl)
    SESSION.commit()
    print("Added artist account:", site_account_text)
    return True


def AddArtistProfile(artist, profile_text):
    print("AddArtistProfile")
    current_profiles = [descr.body for descr in artist.profiles]
    if profile_text in current_profiles:
        return False
    descr = Description.query.filter_by(body=profile_text).first()
    if descr is None:
        descr = Description(body=profile_text)
    artist.profiles.append(descr)
    SESSION.commit()
    print("Added artist profile.")
    return True


def AddArtistWebpages(artist, webpages, commit=True):
    print("AddArtistWebpages")
    artist_urls = []
    new_urls = []
    for url in webpages:
        artist_url = ArtistUrl.query.filter_by(artist_id=artist.id, url=url).first()
        if artist_url is None:
            data = {
                'artist_id': artist.id,
                'url': url,
                'active': True,
            }
            artist_url = ArtistUrl(**data)
            new_urls.append(artist_url)
        artist_urls.append(artist_url)
    if commit and len(new_urls):
        SESSION.add_all(new_urls)
        SESSION.commit()
        print("Added artist webpages:", [webpage.url for webpage in new_urls])
    return artist_urls


def GetTwitterUserWebpages(twuser):
    webpages = set()
    url_entries = SafeGet(twuser, 'entities', 'url', 'urls') or []
    for entry in url_entries:
        if 'expanded_url' in entry:
            webpages.add(entry['expanded_url'])
        elif 'url' in entry:
            webpages.add(entry['url'])

    url_entries = SafeGet(twuser, 'entities', 'description', 'urls') or []
    for entry in url_entries:
        if 'expanded_url' in entry:
            webpages.add(entry['expanded_url'])
        elif 'url' in entry:
            webpages.add(entry['url'])
    return list(webpages)


def ConvertText(twitter_data, key, *subkeys):
    text = twitter_data[key]
    url_entries = SafeGet(twitter_data, 'entities', *subkeys) or []
    for url_entry in reversed(url_entries):
        replace_url = url_entry['expanded_url']
        start_index, end_index = url_entry['indices']
        text = text[:start_index] + replace_url + text[end_index:]
    return text


def GetTweetText(twitter_data):
    text = ConvertText(twitter_data, 'full_text', 'urls')
    return SHORT_URL_REPLACE_RG.sub('', text).strip()


def GetUserDescription(twitter_data):
    return ConvertText(twitter_data, 'description', 'description', 'urls')


def CreateArtistFromUser(twuser, commit=True):
    current_time = GetCurrentTime()
    data = {
        'site_id': Site.TWITTER.value,
        'site_artist_id': int(twuser['id_str']),
        'site_created': ProcessTwitterTimestring(twuser['created_at']),
        'requery': GetCurrentTime() + datetime.timedelta(days=1),
        'created': current_time,
        'updated': current_time,
    }
    artist = Artist(**data)
    if commit:
        SESSION.add(artist)
        SESSION.commit()
        AddArtistName(artist, twuser['name'])
        AddArtistSiteAccount(artist, twuser['screen_name'])
        AddArtistProfile(artist, GetUserDescription(twuser))
        AddArtistWebpages(artist, GetTwitterUserWebpages(twuser))
    return artist


def CreateArtistFromParameters(params):
    if 'site_created' in params:
        try:
            params['site_created'] = ProcessTwitterTimestring(params['site_created'])
        except Exception:
            del params['site_created']
    return BASE.CreateArtistFromParameters(params, Site.TWITTER.value)


#   Update


def UpdateIllustFromTweet(illust, tweet):
    illust.score = tweet['favorite_count']
    illust.site_data.retweets = tweet['retweet_count']
    illust.site_data.replies = tweet['reply_count'] if 'reply_count' in tweet else illust.site_data.replies
    illust.site_data.quotes = tweet['quote_count'] if 'quote_count' in tweet else illust.site_data.quotes
    dirty = SESSION.is_modified(illust) or SESSION.is_modified(illust.site_data)
    UpdateTimestamps(illust, dirty)
    if dirty:
        print("Committing updates for illust #", illust.id)
    else:
        print("No changes detected for illust #", illust.id)
    # Must update the requery if nothing else
    SESSION.commit()


def UpdateArtistFromUser(artist, twuser):
    print("UpdateArtistFromUser")
    dirty = False
    if artist.created is None:
        artist.created = ProcessTwitterTimestring(twuser['created_at'])
        dirty = True
    dirty = AddArtistName(artist, twuser['name']) or dirty
    dirty = AddArtistSiteAccount(artist, twuser['screen_name']) or dirty
    dirty = AddArtistProfile(artist, GetUserDescription(twuser)) or dirty
    dirty = UpdateArtistWebpages(artist, twuser) or dirty
    UpdateTimestamps(artist, dirty)
    if dirty:
        print("Committing updates for artist #", artist.id)
    else:
        print("No changes detected for artist #", artist.id)
    # Must update the requery if nothing else
    SESSION.commit()


def UpdateArtistWebpages(artist, twuser):
    print("UpdateArtistWebpages")
    current_webpages = artist.webpages
    active_webpages = AddArtistWebpages(artist, GetTwitterUserWebpages(twuser), False)
    active_urls = [webpage.url for webpage in active_webpages]
    print("Current:\n", current_webpages)
    print("Active:\n", active_webpages)
    for webpage in active_webpages:
        if webpage.id is not None and webpage.active:
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
    if SESSION.dirty or SESSION.new:
        SESSION.commit()
        print("Modified webpages for artist #", artist.id)
        return True
    return False


# OTHER


def CacheTimelineData(twitter_data, type):
    tweet_ids = list(map(int, twitter_data.keys()))
    cache_data = GetApiData(tweet_ids, type)
    for key in twitter_data:
        data_id = int(key)
        cache_item = next(filter(lambda x: x.data_id == data_id, cache_data), None)
        if not cache_item:
            print("CacheTimelineData - adding cache item:", type, data_id)
            data = {
                'site_id': Site.TWITTER.value,
                'type': type,
                'data_id': data_id,
            }
            cache_item = ApiData(**data)
            SESSION.add(cache_item)
        else:
            print("CacheTimelineData - updating cache item:", type, data_id, cache_item.id)
        cache_item.data = twitter_data[key]
        cache_item.expires = DaysFromNow(1)
    SESSION.commit()


def CacheLookupData(twitter_data, type):
    twitter_ids = [int(data['id_str']) for data in twitter_data]
    cache_data = GetApiData(twitter_ids, type)
    for data_item in twitter_data:
        data_id = int(data_item['id_str'])
        cache_item = next(filter(lambda x: x.data_id == data_id, cache_data), None)
        if not cache_item:
            print("CacheLookupData - adding cache item:", type, data_id)
            data = {
                'site_id': Site.TWITTER.value,
                'type': type,
                'data_id': data_id,
            }
            cache_item = ApiData(**data)
            SESSION.add(cache_item)
        else:
            print("CacheTimelineData - updating cache item:", type, data_id, cache_item.id)
        cache_item.data = data_item
        cache_item.expires = DaysFromNow(1)
    SESSION.commit()


def GetSiteIllust(site_illust_id):
    return Illust.query.filter_by(site_id=Site.TWITTER.value, site_illust_id=site_illust_id).first()


def GetSiteArtist(site_artist_id):
    return Artist.query.filter_by(site_id=Site.TWITTER.value, site_artist_id=site_artist_id).first()


def GetApiData(data_ids, type):
    cache_data = []
    for i in range(0, len(data_ids), 100):
        sublist = data_ids[i: i + 100]
        cache_data += _GetApiData(data_ids, type)
    return cache_data


def _GetApiData(data_ids, type):
    q = ApiData.query
    q = q.filter_by(site_id=Site.TWITTER.value, type=type)
    if len(data_ids) == 1:
        q = q.filter_by(data_id=data_ids[0])
    else:
        q = q.filter(ApiData.data_id.in_(data_ids))
    q = q.filter(ApiData.expires > GetCurrentTime())
    return q.all()


def GetApiArtist(site_artist_id):
    cache = GetApiData([site_artist_id], 'artist')
    return cache[0].data if len(cache) else None


def GetApiIllust(site_illust_id):
    cache = GetApiData([site_illust_id], 'illust')
    return cache[0].data if len(cache) else None


"""
def GetApiArtists(site_illust_ids):
    q = ApiData.query
    q = q.filter_by(site_id=Site.TWITTER.value, type='artist')
    q = q.filter(ApiData.data_id.in_(site_illust_ids))
    q = q.filter(ApiData.expires > GetCurrentTime())
    return q.all()
"""
