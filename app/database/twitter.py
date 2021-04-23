# APP/DATABASE/PIXIV.PY


# ##PYTHON IMPORTS
import re
import time
import urllib
import datetime


# ##LOCAL IMPORTS
from . import base
from . import models
from ..logical.utility import ProcessTimestamp, GetCurrentTime, SafeGet
from ..sources.pixiv import SITE_ID,IMAGE_SITE_ID
from ..config import workingdirectory, jsonfilepath
from ..sites import Site, GetSiteId, GetSiteDomain


# ##GLOBAL VARIABLES

ONE_DAY = 60 * 60 * 24

DATABASE_FILE = workingdirectory + jsonfilepath + 'prebooru-pixiv-data.json'

DATABASE_TABLES = ['artists', 'illusts']

DATABASE = None
ID_INDEXES = base.InitializeIDIndexes(DATABASE_TABLES)
OTHER_INDEXES = {
    'artists': {
        'artist_id': {}
    },
    'illusts': {
        'illust_id': {}
    }
}

SHORT_URL_REPLACE_RG = re.compile(r"""
https?://t\.co                         # Hostname
/ [\w-]+                               # Account
""", re.X | re.IGNORECASE)


# ##FUNCTIONS

#   I/O

def LoadDatabase():
    global DATABASE
    DATABASE = base.LoadDatabaseFile("PIXIV", DATABASE_FILE, DATABASE_TABLES, True)
    base.SetIndexes(ID_INDEXES, OTHER_INDEXES, DATABASE)


def SaveDatabase():
    base.SaveDatabaseFile("PIXIV", DATABASE, DATABASE_FILE, True)


#   Create


def ProcessUTCTimestring(time_string):
    return datetime.datetime.utcfromtimestamp(ProcessTimestamp(time_string))

def ProcessTwitterTimestring(time_string):
    return datetime.datetime.strptime(time_string, '%a %b %d %H:%M:%S +0000 %Y')


"""
    'images': [
    {
        'url': urllib.parse.urlparse(pixiv_data['urls']['original']).path,
        'width': pixiv_data['width'],
        'height': pixiv_data['height']
    }],
    'tags': [tag['tag'] for tag in pixiv_data['tags']['tags']],
"""

def UpdateRequery(instance, commit=True):
    instance.requery = GetCurrentTime() + datetime.timedelta(days=1)
    if commit:
        SESSION.add(instance)
        SESSION.commit()
    return instance

def ProcessIllustData(tweet, user):
    print("ProcessIllustData")
    artist = models.Artist.query.filter_by(site_id=Site.TWITTER.value, site_artist_id=int(tweet['user_id_str'])).first()
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
        #'bookmarks': twitter_data['retweet_count'],
        'score': tweet['favorite_count'],
        #'replies': twitter_data['reply_count'],
        'requery': GetCurrentTime() + datetime.timedelta(days=1),
        'created': current_time,
        'updated': current_time,
    }
    illust = models.Illust(**data)
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
    site_data = models.TwitterData(**data)
    SESSION.add(site_data)
    SESSION.commit()

def GetDBTags(tweet):
    print("GetDBTags")
    def FindOrCommitTag(name):
        tag = models.Tag.query.filter_by(name=name).first()
        if tag is None:
            tag = models.Tag(name=name)
            SESSION.add(tag)
            SESSION.commit()
        return tag
    tag_data = SafeGet(tweet, 'entities', 'hashtags') or []
    tags = []
    for entry in tag_data:
        tags.append(FindOrCommitTag(entry['text']))
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
        url = parse.path if site_id != 0 else url
        data = {
            'site_id': site_id,
            'url': url,
            'width': entry['original_info']['width'],
            'height': entry['original_info']['height'],
            'illust_id': illust.id,
            'order': i,
            'active': True,
        }
        illust_url = models.IllustUrl(**data)
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
        artist_url = models.ArtistUrl.query.filter_by(artist_id=artist_id, url=page).first()
        if artist_url is None:
            data = {
                'artist_id': artist_id,
                'url': page,
                'active': True,
            }
            artist_url = models.ArtistUrl(**data)
            new_urls.append(artist_url)
        artist_urls.append(artist_url)
    if commit and len(new_urls):
        SESSION.add_all(new_urls)
    return artist_urls


def ConvertText(twitter_data, key, *subkeys):
    text = twitter_data[key]
    url_entries = SafeGet(twitter_data, 'entities', *subkeys) or []
    for url_entry in reversed(url_entries):
        check_url = url_entry['url']
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
    artist = models.Artist(**data)
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
    current_webpages = models.ArtistUrl.query.filter_by(artist_id=artist.id).all()
    active_webpages = AddArtistWebpages(twitter_data, artist.id, False)
    active_urls = [webpage.url for webpage in active_webpages]
    update_webpages = []
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


#   Misc


def FindByID(table, id):
    return base.FindByID(ID_INDEXES, table, id)


def FindBy(table, key, value):
    return base.FindBy(OTHER_INDEXES, DATABASE, table, key, value)


def GetCurrentIndex(type):
    return base.GetCurrentIndex(DATABASE, type)



########################

def Initialize(db):
    global DB, SESSION
    DB = db
    SESSION = db.session


"""
def InitializeModels(db):
    global IllustUrl, Illust, IllustTag, Artist, ArtistUrl, Tag
    class Tag(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.Unicode(255), nullable=False)
        illust_tags = db.relationship('IllustTag', backref='tag', lazy=True)
    
    class ArtistUrl(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
        url = db.Column(db.String(255), nullable=False)
    
    class IllustUrl(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        illust_id = db.Column(db.Integer, db.ForeignKey('illust.id'), nullable=False)
        url = db.Column(db.String(255), nullable=False)
        width = db.Column(db.Integer, nullable=True)
        height = db.Column(db.Integer, nullable=True)
        order = db.Column(db.Integer, nullable=False)
    
    class IllustTag(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        illust_id = db.Column(db.Integer, db.ForeignKey('illust.id'), nullable=False)
        tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), nullable=False)
    
    class Illust(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        site_id = db.Column(db.Integer, nullable=False)
        illust_id = db.Column(db.Integer, nullable=False)
        title = db.Column(db.UnicodeText, nullable=True)
        description = db.Column(db.UnicodeText, nullable=True)
        created = db.Column(db.DateTime(timezone=False), nullable=True)
        uploaded = db.Column(db.DateTime(timezone=False), nullable=True)
        tags = db.relationship('IllustTag', backref='illust', lazy=True)
        urls = db.relationship('IllustUrl', backref='illust', lazy=True)
        artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
        pages = db.Column(db.Integer, nullable=True)
        bookmarks = db.Column(db.Integer, nullable=False)
        likes = db.Column(db.Integer, nullable=False)
        replies = db.Column(db.Integer, nullable=False)
        views = db.Column(db.Integer, nullable=True)
        requery = db.Column(db.DateTime(timezone=False), nullable=False)
    
    class Artist(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        site_id = db.Column(db.Integer, nullable=False)
        artist_id = db.Column(db.Integer, nullable=False)
        site_account = db.Column(db.String, nullable=False)
        illusts = db.relationship('Illust', backref='artist', lazy=True)
        name = db.Column(db.Unicode(255), nullable=False)
        profile = db.Column(db.UnicodeText, nullable=False)
        webpages = db.relationship('ArtistUrl', backref='artist', lazy=True)
        requery = db.Column(db.DateTime(timezone=False))
"""
