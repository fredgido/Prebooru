# APP/DATABASE/PIXIV.PY


# ##PYTHON IMPORTS
import time
import urllib
import datetime


# ##LOCAL IMPORTS
from . import base
from . import models
from ..logical.utility import ProcessTimestamp, GetCurrentTime
from ..sources.pixiv import SITE_ID,IMAGE_SITE_ID
from ..config import workingdirectory, jsonfilepath
from ..sites import Site, GetSiteId


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

def ProcessIllustData(pixiv_data):
    artist = models.Artist.query.filter_by(site_id=Site.PIXIV.value, site_artist_id=int(pixiv_data['userId'])).first()
    if artist is None:
        artist = CreateArtistFromIllust(pixiv_data)
    illust = CreateIllustFromIllust(pixiv_data, artist.id)
    return illust
def CreateIllustFromIllust(pixiv_data, artist_id, commit=True):
    current_time = GetCurrentTime()
    sub_data = pixiv_data['userIllusts'][pixiv_data['illustId']]
    data = {
        'site_id': Site.PIXIV.value,
        'site_illust_id': int(pixiv_data['illustId']),
        'site_created': ProcessUTCTimestring(pixiv_data['createDate']),
        'site_uploaded': ProcessUTCTimestring(pixiv_data['uploadDate']),
        'site_updated': ProcessUTCTimestring(sub_data['updateDate']),
        'artist_id': artist_id,
        'title': pixiv_data['title'],
        'description': pixiv_data['extraData']['meta']['twitter']['description'],
        'pages': pixiv_data['pageCount'],
        'bookmarks': pixiv_data['bookmarkCount'],
        'likes': pixiv_data['likeCount'],
        'replies': pixiv_data['responseCount'],
        'views': pixiv_data['viewCount'],
        'requery': None,
        'created': current_time,
        'updated': current_time,
    }
    illust = models.Illust(**data)
    if commit:
        SESSION.add(illust)
        SESSION.commit()
        CreateIllustUrlFromIllust(pixiv_data, illust.id)
        tags = GetDBTags(pixiv_data)
        if len(tags):
            illust.tags.extend(tags)
            SESSION.add(illust)
            SESSION.commit()
    return illust


def GetDBTags(pixiv_data):
    def FindOrCommitTag(name):
        tag = models.Tag.query.filter_by(name=name).first()
        if tag is None:
            tag = models.Tag(name=tag_data['tag'])
            SESSION.add(tag)
            SESSION.commit()
        return tag
    tags = []
    for tag_data in pixiv_data['tags']['tags']:
        tags.append(FindOrCommitTag(tag_data['tag']))
    if pixiv_data['isOriginal']:
        tags.append(FindOrCommitTag('original'))
    return tags

def CreateIllustUrlFromIllust(pixiv_data, illust_id, commit=True):
    parse = urllib.parse.urlparse(pixiv_data['urls']['original'])
    site_id = GetSiteId(parse.netloc)
    url = parse.path if site_id != 0 else url
    data = {
        'site_id': site_id,
        'url': url,
        'width': pixiv_data['width'],
        'height': pixiv_data['height'],
        'illust_id': illust_id,
        'order': 0,
        'active': True,
    }
    illust_url = models.IllustUrl(**data)
    if commit:
        SESSION.add(illust_url)
        SESSION.commit()
    return illust_url


def CreateWebpagesFromUser(pixiv_data, artist_id, commit=True):
    artist_urls = []
    new_urls = []
    webpages = set()
    if pixiv_data['webpage'] is not None:
        webpages.add(pixiv_data['webpage'])
    for site in pixiv_data['social']:
        webpages.add(pixiv_data['social'][site]['url'])
    for page in webpages:
        artist_url = models.ArtistUrl.query.filter_by(artist_id=artist_id, url=page).first()
        if artist_url is None:
            data = {
                'artist_id': artist_id,
                'url': page,
            }
            artist_url = models.ArtistUrl(**data)
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
    artist = models.Artist(**data)
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
    artist = models.Artist(**data)
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
    first_url = models.IllustUrl.query.filter_by(illust_id=illust.id, order=0, active=True).first()
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
        url = parse.path if site_id != 0 else url
        active_url = models.IllustUrl.query.filter_by(illust_id=illust.id, order=i, active=True).first()
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
        image_url = models.IllustUrl(**data)
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
    current_webpages = models.ArtistUrl.query.filter_by(artist_id=artist.id).all()
    active_webpages = CreateWebpagesFromUser(pixiv_data, artist.id, False)
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
