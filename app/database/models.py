import datetime
from typing import List, _GenericAlias
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from sqlalchemy.orm import declared_attr

from .. import data

def DateTimeOrNull(value):
    return value if value is None else datetime.datetime.isoformat(value)

def IntOrNone(data):
    return data if data is None else int(data)

def StrOrNone(data):
    return data if data is None else str(data)

def InitializeModels(db):
    global IllustUrl, Illust, IllustTag, Artist, ArtistUrl, Tag, IllustTags, Error, UploadUrl, Upload, Post, Subscription, TwitterData, PixivData
    
    class JsonModel(db.Model):
        __abstract__ = True
        def to_json(self):
            fields = self.__dataclass_fields__
            data = {}
            for key in fields:
                value = getattr(self, key)
                type_func = fields[key].type
                #print(key, value, type_func)
                if type_func is None:
                    data[key] = None
                elif 'to_json' in dir(type_func):
                    data[key] = value.to_json()
                elif type_func == List:
                    data[key] = [t.to_json() for t in value]
                elif isinstance(type_func, _GenericAlias):
                    subtype_func = type_func.__args__[0]
                    data[key] = [subtype_func(t.to_json()) for t in value]
                else:
                    data[key] = type_func(value)
            return data
    
    IllustTags = db.Table('illust_tags',
        db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
        db.Column('illust_id', db.Integer, db.ForeignKey('illust.id'), primary_key=True),
    )

    @dataclass
    class Tag(JsonModel):
        id: int
        name: str
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.Unicode(255), nullable=False)
    
    @dataclass
    class ArtistUrl(db.Model):
        id: int
        artist_id: int
        url: str
        active: bool
        id = db.Column(db.Integer, primary_key=True)
        artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
        url = db.Column(db.String(255), nullable=False)
        active = db.Column(db.Boolean, nullable=False)
    
    @dataclass
    class IllustUrl(JsonModel):
        id: int
        site_id: int
        url: str
        width: IntOrNone
        height: IntOrNone
        order: int
        illust_id: int
        active: bool
        id = db.Column(db.Integer, primary_key=True)
        site_id = db.Column(db.Integer, nullable=False)
        url = db.Column(db.String(255), nullable=False)
        width = db.Column(db.Integer, nullable=True)
        height = db.Column(db.Integer, nullable=True)
        order = db.Column(db.Integer, nullable=False)
        illust_id = db.Column(db.Integer, db.ForeignKey('illust.id'), nullable=False)
        active = db.Column(db.Boolean, nullable=False)
    
    """
    class IllustTag(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        illust_id = db.Column(db.Integer, db.ForeignKey('illust.id'), nullable=False)
        tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), nullable=False)
    """
    
    def RemoveKeys(data, keylist):
        return {k:data[k] for k in data if k not in keylist}
    
    @dataclass
    class SiteData(JsonModel):
        __tablename__ = 'site_data'
        id: int
        illust_id: int
        type: str
        id = db.Column(db.Integer, primary_key=True)
        illust_id = db.Column(db.Integer, db.ForeignKey('illust.id'), nullable=False)
        type = db.Column(db.String(50))
        __mapper_args__ = {
            'polymorphic_identity': 'site_data',
            "polymorphic_on": type
        }
    
    @dataclass
    class PixivData(SiteData):
        __tablename__ = 'pixiv_data'
        site_uploaded: DateTimeOrNull
        site_updated: DateTimeOrNull
        title: str
        bookmarks: int
        replies: int
        views: int
        site_uploaded = db.Column(db.DateTime(timezone=False), nullable=True)
        site_updated = db.Column(db.DateTime(timezone=False), nullable=True)
        title = db.Column(db.UnicodeText, nullable=True)
        bookmarks = db.Column(db.Integer, nullable=True)
        @declared_attr
        def replies(cls):
            return SiteData.__table__.c.get('replies', db.Column(db.Integer, nullable=True))
        views = db.Column(db.Integer, nullable=True)
        __mapper_args__ = {
            'polymorphic_identity': 'pixiv_data',
        }
    
    @dataclass
    class TwitterData(SiteData):
        __tablename__ = 'twitter_data'
        retweets: int
        replies: int
        quotes: int
        retweets = db.Column(db.Integer, nullable=True)
        @declared_attr
        def replies(cls):
            return SiteData.__table__.c.get('replies', db.Column(db.Integer, nullable=True))
        quotes = db.Column(db.Integer, nullable=True)
        __mapper_args__ = {
            'polymorphic_identity': 'twitter_data',
        }
    
    @dataclass
    class Illust(JsonModel):
        id: int
        site_id: int
        site_illust_id: int
        site_created: DateTimeOrNull
        description: str
        tags: List[lambda x: x['name']]
        urls: List[lambda x: RemoveKeys(x, ['id', 'illust_id'])]
        artist_id: int
        pages: int
        score: int
        site_data: lambda x: RemoveKeys(x.to_json(), ['id', 'illust_id', 'type'])
        requery: DateTimeOrNull
        created: datetime.datetime.isoformat
        updated: datetime.datetime.isoformat
        id = db.Column(db.Integer, primary_key=True)
        site_id = db.Column(db.Integer, nullable=False)
        site_illust_id = db.Column(db.Integer, nullable=False)
        site_created = db.Column(db.DateTime(timezone=False), nullable=True)
        description = db.Column(db.UnicodeText, nullable=True)
        tags = db.relationship('Tag', secondary=IllustTags, lazy='subquery', backref=db.backref('illusts', lazy=True))
        urls = db.relationship('IllustUrl', backref='illust', lazy=True, cascade="all, delete")
        artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
        pages = db.Column(db.Integer, nullable=True)
        score = db.Column(db.Integer, nullable=True)
        site_data = db.relationship('SiteData', backref='illust', lazy=True, uselist=False)
        requery = db.Column(db.DateTime(timezone=False), nullable=True)
        created = db.Column(db.DateTime(timezone=False), nullable=False)
        updated = db.Column(db.DateTime(timezone=False), nullable=False)
    
    @dataclass
    class Artist(db.Model):
        id: int
        site_id: int
        site_artist_id: IntOrNone
        site_account: StrOrNone
        name: str
        profile: str
        webpages: List[ArtistUrl]
        requery: DateTimeOrNull
        created: datetime.datetime.isoformat
        updated: datetime.datetime.isoformat
        id = db.Column(db.Integer, primary_key=True)
        site_id = db.Column(db.Integer, nullable=False)
        site_artist_id = db.Column(db.Integer, nullable=True)
        site_account = db.Column(db.String(255), nullable=True)
        name = db.Column(db.Unicode(255), nullable=False)
        profile = db.Column(db.UnicodeText, nullable=False)
        illusts = db.relationship('Illust', lazy=True, backref=db.backref('artist', lazy=True))
        webpages = db.relationship('ArtistUrl', backref='artist', lazy=True)
        requery = db.Column(db.DateTime(timezone=False), nullable=True)
        created = db.Column(db.DateTime(timezone=False), nullable=False)
        updated = db.Column(db.DateTime(timezone=False), nullable=False)
    
    @dataclass
    class Error(JsonModel):
        id: int
        module: str
        message: str
        created: datetime.datetime.isoformat
        id = db.Column(db.Integer, primary_key=True)
        module = db.Column(db.String(255), nullable=False)
        message = db.Column(db.UnicodeText, nullable=False)
        created = db.Column(db.DateTime(timezone=False), nullable=False)
    
    PostIllustUrls = db.Table('post_illust_urls',
        db.Column('illust_url_id', db.Integer, db.ForeignKey('illust_url.id'), primary_key=True),
        db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    )
    
    PostErrors = db.Table('post_errors',
        db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
        db.Column('error_id', db.Integer, db.ForeignKey('error.id'), primary_key=True),
    )
    
    @dataclass
    class Post(JsonModel):
        id: int
        width: int
        height: int
        file_ext: str
        md5: str
        size: int
        illust_urls: List[lambda x: RemoveKeys(x, ['height', 'width'])]
        file_url: str
        sample_url: str
        preview_url: str
        errors: List
        created: datetime.datetime.isoformat
        
        @property
        def file_url(self):
            return data.NetworkDirectory('data', self.md5) + self.md5 + '.' + self.file_ext
        
        @property
        def sample_url(self):
            return data.NetworkDirectory('sample', self.md5) + self.md5 + '.' + self.file_ext if data.HasSample(self.width, self.height) else self.file_url
        
        @property
        def preview_url(self):
            return data.NetworkDirectory('preview', self.md5) + self.md5 + '.' + self.file_ext if data.HasPreview(self.width, self.height) else self.file_url
        
        id = db.Column(db.Integer, primary_key=True)
        width = db.Column(db.Integer, nullable=False)
        height = db.Column(db.Integer, nullable=False)
        file_ext = db.Column(db.String(6), nullable=False)
        md5 = db.Column(db.String(255), nullable=False)
        size = db.Column(db.Integer, nullable=False)
        illust_urls = db.relationship('IllustUrl', secondary=PostIllustUrls, lazy='subquery', backref=db.backref('post', uselist=False, lazy=True))
        errors = db.relationship('Error', secondary=PostErrors, lazy=True)
        created = db.Column(db.DateTime(timezone=False), nullable=False) 
    
    @dataclass
    class UploadUrl(JsonModel):
        id: int
        url: str
        id = db.Column(db.Integer, primary_key=True)
        url = db.Column(db.String(255), nullable=False)
    
    UploadUrls = db.Table('upload_urls',
        db.Column('upload_id', db.Integer, db.ForeignKey('upload.id'), primary_key=True),
        db.Column('upload_url_id', db.Integer, db.ForeignKey('upload_url.id'), primary_key=True),
    )
    UploadErrors = db.Table('upload_errors',
        db.Column('upload_id', db.Integer, db.ForeignKey('upload.id'), primary_key=True),
        db.Column('error_id', db.Integer, db.ForeignKey('error.id'), primary_key=True),
    )
    UploadPosts = db.Table('upload_posts',
        db.Column('upload_id', db.Integer, db.ForeignKey('upload.id'), primary_key=True),
        db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    )
    
    @dataclass
    class Upload(JsonModel):
        id: int
        uploader_id: int
        subscription_id: IntOrNone
        request_url: StrOrNone
        referrer_url: StrOrNone
        type: str
        status: str
        successes: int
        failures: int
        #posts: List[lambda x: x['id']]
        image_urls: List
        post_ids: lambda x: x
        errors: List
        
        @property
        def post_ids(self):
            return [post.id for post in self.posts]
        
        created: datetime.datetime.isoformat
        id = db.Column(db.Integer, primary_key=True)
        uploader_id = db.Column(db.Integer, nullable=False)
        request_url = db.Column(db.String(255), nullable=True)
        referrer_url = db.Column(db.String(255), nullable=True)
        successes = db.Column(db.Integer, nullable=False)
        failures = db.Column(db.Integer, nullable=False)
        type = db.Column(db.String(255), nullable=False)
        status = db.Column(db.String(255), nullable=False)
        subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'), nullable=True)
        image_urls = db.relationship('UploadUrl', secondary=UploadUrls, lazy='subquery', uselist=True, backref=db.backref('upload', lazy=True))
        posts = db.relationship('Post', secondary=UploadPosts, lazy=True)
        errors = db.relationship('Error', secondary=UploadErrors, lazy=True)
        created = db.Column(db.DateTime(timezone=False), nullable=False)
    
    @dataclass
    class Subscription(db.Model):
        id: int
        artist_id: int
        #user_id: int
        requery: DateTimeOrNull
        created: datetime.datetime.isoformat
        id = db.Column(db.Integer, primary_key=True)
        artist_id = db.Column(db.Integer, nullable=False)
        #user_id = db.Column(db.Integer, nullable=True)
        uploads = db.relationship('Upload', backref='subscription', lazy=True)
        requery = db.Column(db.DateTime(timezone=False), nullable=True)
        created = db.Column(db.DateTime(timezone=False), nullable=False)
    
    