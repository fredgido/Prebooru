# APP/DATABASE/TWITTER.PY

# ##PYTHON IMPORTS
import re
import urllib
import datetime


# ##LOCAL IMPORTS
from .. import session as SESSION
from ..models import ArtistUrl, Artist, Tag, IllustUrl, TwitterData, Illust
from ..logical.utility import GetCurrentTime, SafeGet
from ..sites import Site, GetSiteId


# ##GLOBAL VARIABLES


SHORT_URL_REPLACE_RG = re.compile(r"""
https?://t\.co                         # Hostname
/ [\w-]+                               # Account
""", re.X | re.IGNORECASE)


# ##FUNCTIONS


def ProcessTwitterTimestring(time_string):
    return datetime.datetime.strptime(time_string, '%a %b %d %H:%M:%S +0000 %Y')


def UpdateRequery(instance, commit=True):
    instance.requery = GetCurrentTime() + datetime.timedelta(days=1)
    if commit:
        SESSION.add(instance)
        SESSION.commit()
    return instance


def ProcessIllustData(tweet, user):
    print("ProcessIllustData")
    artist = Artist.query.filter_by(site_id=Site.TWITTER.value, site_artist_id=int(tweet['user_id_str'])).first()
    if artist is None:
        artist = CreateArtistFromUser(user)
    elif artist.requery is None or artist.requery < GetCurrentTime():
        UpdateArtistFromUser(artist, user)
    illust = CreateIllustFromIllust(tweet, artist.id)
    return illust


def CreateIllustFromIllust(tweet, artist_id, commit=True):
    print("CreateIllustFromIllust")
    current_time = GetCurrentTime()
    data = {
        'site_id': Site.TWITTER.value,
        'site_illust_id': int(tweet['id_str']),
        'site_created': ProcessTwitterTimestring(tweet['created_at']),
        'artist_id': artist_id,
        'description': GetTweetText(tweet),
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
        AddIllustTags(illust, tweet)
        AddIllustUrls(illust, tweet)
    return illust


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
        'replies': tweet['reply_count'],
        'quotes': tweet['quote_count'],
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
    for entry in tag_data:
        tagname = entry['text'].lower()
        tags.append(FindOrCommitTag(tagname))
    if len(tags):
        SESSION.commit()
    return tags


def AddIllustUrls(illust, tweet, commit=True):
    print("AddIllustUrls")
    url_data = SafeGet(tweet, 'entities', 'media') or []
    illust_urls = []
    for i in range(0, len(url_data)):
        entry = url_data[i]
        parse = urllib.parse.urlparse(entry['media_url_https'])
        site_id = GetSiteId(parse.netloc)
        url = parse.path if site_id != 0 else entry['media_url_https']
        data = {
            'site_id': site_id,
            'url': url,
            'width': entry['original_info']['width'],
            'height': entry['original_info']['height'],
            'illust_id': illust.id,
            'order': i,
            'active': True,
        }
        illust_url = IllustUrl(**data)
        illust_urls.append(illust_url)
    if commit:
        SESSION.add_all(illust_urls)
        SESSION.commit()
    return illust_urls


def AddArtistWebpages(user, artist_id, commit=True):
    print("AddArtistWebpages")
    artist_urls = []
    new_urls = []
    webpages = set()
    url_entries = SafeGet(user, 'entities', 'url', 'urls') or []
    for entry in url_entries:
        webpages.add(entry['expanded_url'])
    url_entries = SafeGet(user, 'entities', 'description', 'urls') or []
    for entry in url_entries:
        webpages.add(entry['expanded_url'])
    for page in webpages:
        artist_url = ArtistUrl.query.filter_by(artist_id=artist_id, url=page).first()
        if artist_url is None:
            data = {
                'artist_id': artist_id,
                'url': page,
                'active': True,
            }
            artist_url = ArtistUrl(**data)
            new_urls.append(artist_url)
        artist_urls.append(artist_url)
    if commit and len(new_urls):
        SESSION.add_all(new_urls)
    return artist_urls


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


def CreateArtistFromUser(twitter_data, commit=True):
    current_time = GetCurrentTime()
    data = {
        'site_id': Site.TWITTER.value,
        'site_artist_id': int(twitter_data['id_str']),
        'site_account': twitter_data['screen_name'],
        'name': twitter_data['name'],
        'profile': GetUserDescription(twitter_data),
        'requery': None,
        'created': current_time,
        'updated': current_time,
    }
    artist = Artist(**data)
    if commit:
        SESSION.add(artist)
        SESSION.commit()
        AddArtistWebpages(twitter_data, artist.id)
    return artist


#   Update


def UpdateArtistFromUser(artist, twitter_data):
    print("UpdateArtistFromUser")
    temp_artist = CreateArtistFromUser(twitter_data, False)
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
    active_webpages = AddArtistWebpages(twitter_data, artist.id, False)
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


def GetIllust(site_illust_id):
    return Illust.query.filter_by(site_id=Site.TWITTER.value, site_illust_id=site_illust_id).first()


def GetArtist(artist_id):
    return Artist.query.filter_by(id=artist_id).first(), None
