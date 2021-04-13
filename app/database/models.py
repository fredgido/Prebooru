import datetime
from dataclasses import dataclass

def DateTimeOrNull(value):
    return value if value is None else datetime.datetime.isoformat(value)

def IntOrNone(data):
    return data if data is None else int(data)

def StrOrNone(data):
    return data if data is None else str(data)

def InitializeModels(db):
    global IllustUrl, Illust, IllustTag, Artist, ArtistUrl, Tag, IllustTags, Error, Upload, Post, Subscription
    
    IllustTags = db.Table('illust_tags',
        db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
        db.Column('illust_id', db.Integer, db.ForeignKey('illust.id'), primary_key=True),
    )

    @dataclass
    class Tag(db.Model):
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
    class IllustUrl(db.Model):
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
    
    @dataclass
    class Illust(db.Model):
        id: int
        site_id: int
        site_illust_id: int
        site_created: DateTimeOrNull
        site_uploaded: DateTimeOrNull
        site_updated: DateTimeOrNull
        title: str
        description: str
        tags: Tag
        urls: IllustUrl
        artist_id: int
        pages: int
        bookmarks: int
        likes: int
        replies: int
        views: int
        requery: DateTimeOrNull
        created: datetime.datetime.isoformat
        updated: datetime.datetime.isoformat
        id = db.Column(db.Integer, primary_key=True)
        site_id = db.Column(db.Integer, nullable=False)
        site_illust_id = db.Column(db.Integer, nullable=False)
        site_created = db.Column(db.DateTime(timezone=False), nullable=True)
        site_uploaded = db.Column(db.DateTime(timezone=False), nullable=True)
        site_updated = db.Column(db.DateTime(timezone=False), nullable=True)
        title = db.Column(db.UnicodeText, nullable=True)
        description = db.Column(db.UnicodeText, nullable=True)
        #tags = db.relationship('IllustTag', backref='illust', lazy=True)
        tags = db.relationship('Tag', secondary=IllustTags, lazy='subquery', backref=db.backref('illusts', lazy=True))
        urls = db.relationship('IllustUrl', backref='illust', lazy=True)
        artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
        pages = db.Column(db.Integer, nullable=True)
        bookmarks = db.Column(db.Integer, nullable=False)
        likes = db.Column(db.Integer, nullable=False)
        replies = db.Column(db.Integer, nullable=False)
        views = db.Column(db.Integer, nullable=True)
        posts = db.relationship('Post', backref='illust', lazy=True)
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
        webpages: ArtistUrl
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
        posts = db.relationship('Post', lazy=True, backref=db.backref('artist', lazy=True))
        webpages = db.relationship('ArtistUrl', backref='artist', lazy=True)
        requery = db.Column(db.DateTime(timezone=False), nullable=True)
        created = db.Column(db.DateTime(timezone=False), nullable=False)
        updated = db.Column(db.DateTime(timezone=False), nullable=False)
    
    @dataclass
    class Error(db.Model):
        id: int
        module: str
        message: str
        created: datetime.datetime.isoformat
        id = db.Column(db.Integer, primary_key=True)
        module = db.Column(db.String(255), nullable=False)
        message = db.Column(db.UnicodeText, nullable=False)
        created = db.Column(db.DateTime(timezone=False), nullable=False)
    
    @dataclass
    class Post(db.Model):
        id: int
        illust_id: int
        artist_id: int
        image_key: str
        file_url: str
        md5: str
        size: int
        order: int
        created: datetime.datetime.isoformat
        id = db.Column(db.Integer, primary_key=True)
        image_key = db.Column(db.String(255), nullable=True)
        file_url = db.Column(db.String(255), nullable=False)
        md5 = db.Column(db.String(255), nullable=False)
        size = db.Column(db.Integer, nullable=False)
        order = db.Column(db.Integer, nullable=False)
        illust_id = db.Column(db.Integer, db.ForeignKey('illust.id'), nullable=False)
        artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
        created = db.Column(db.DateTime(timezone=False), nullable=False)
    
    class PostId(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        post_id = db.Column(db.Integer, nullable=False)
        upload_id = db.Column(db.Integer, db.ForeignKey('upload.id'), nullable=False)
    
    @dataclass
    class Upload(db.Model):
        id: int
        uploader_id: int
        subscription_id: IntOrNone
        request_url: StrOrNone
        type: str
        successes: int
        failures: int
        post_ids: PostId
        created: datetime.datetime.isoformat
        id = db.Column(db.Integer, primary_key=True)
        uploader_id = db.Column(db.Integer, nullable=False)
        request_url = db.Column(db.String(255), nullable=True)
        successes = db.Column(db.Integer, nullable=False)
        failures = db.Column(db.Integer, nullable=False)
        type = db.Column(db.String(255), nullable=False)
        subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'), nullable=True)
        post_ids = db.relationship('PostId', lazy=True)
        created = db.Column(db.DateTime(timezone=False), nullable=False)
    
    @dataclass
    class Subscription(db.Model):
        id: int
        artist_id: int
        user_id: int
        requery: DateTimeOrNull
        created: datetime.datetime.isoformat
        id = db.Column(db.Integer, primary_key=True)
        artist_id = db.Column(db.Integer, nullable=False)
        user_id = db.Column(db.Integer, nullable=False)
        uploads = db.relationship('Upload', backref='subscription', lazy=True)
        requery = db.Column(db.DateTime(timezone=False), nullable=True)
        created = db.Column(db.DateTime(timezone=False), nullable=False)
    
    