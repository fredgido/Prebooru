# APP/MODELS/UPLOAD.PY

# ##PYTHON IMPORTS
import datetime
from typing import List
from dataclasses import dataclass
from flask import url_for

# ##LOCAL IMPORTS
from .. import db
from ..logical.utility import UniqueObjects
from .base import JsonModel, IntOrNone, StrOrNone
from .upload_url import UploadUrl
from .post import Post
from .error import Error


# ##GLOBAL VARIABLES

# Many-to-many tables

UploadUrls = db.Table(
    'upload_urls',
    db.Column('upload_id', db.Integer, db.ForeignKey('upload.id'), primary_key=True),
    db.Column('upload_url_id', db.Integer, db.ForeignKey('upload_url.id'), primary_key=True),
)
UploadErrors = db.Table(
    'upload_errors',
    db.Column('upload_id', db.Integer, db.ForeignKey('upload.id'), primary_key=True),
    db.Column('error_id', db.Integer, db.ForeignKey('error.id'), primary_key=True),
)
UploadPosts = db.Table(
    'upload_posts',
    db.Column('upload_id', db.Integer, db.ForeignKey('upload.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
)


# Classes


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
    image_urls: List
    post_ids: lambda x: x
    errors: List
    created: datetime.datetime.isoformat

    id = db.Column(db.Integer, primary_key=True)
    uploader_id = db.Column(db.Integer, nullable=False)
    request_url = db.Column(db.String(255), nullable=True)
    referrer_url = db.Column(db.String(255), nullable=True)
    successes = db.Column(db.Integer, nullable=False)
    failures = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(255), nullable=False)
    media_filepath = db.Column(db.String(255), nullable=True)
    sample_filepath = db.Column(db.String(255), nullable=True)
    illust_url_id = db.Column(db.Integer, db.ForeignKey('illust_url.id'), nullable=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscription.id'), nullable=True)
    image_urls = db.relationship(UploadUrl, secondary=UploadUrls, lazy='subquery', uselist=True, backref=db.backref('upload', lazy=True))
    posts = db.relationship(Post, secondary=UploadPosts, lazy=True)
    errors = db.relationship(Error, secondary=UploadErrors, lazy=True)
    created = db.Column(db.DateTime(timezone=False), nullable=False)

    @property
    def post_ids(self):
        return [post.id for post in self.posts]

    @property
    def show_url(self):
        return url_for("upload.show_html", id=self.id)

    @property
    def site_id(self):
        return self._source.SiteId()

    @property
    def site_illust_id(self):
        return self._source.GetIllustId(self.request_url, self.referrer_url)

    @property
    def illust(self):
        if self._illust is None:
            #print("illust")
            if len(self.posts) == 0:
                return None
            illusts = UniqueObjects(sum([post.illusts for post in self.posts], []))
            self._illust = next(filter(lambda x: (x.site_id == self.site_id) and (x.site_illust_id == self.site_illust_id), illusts), None)
        return self._illust

    @property
    def artist(self):
        return self.illust.artist if self.illust is not None else None

    @property
    def _source(self):
        from ..sources.base import GetSource
        return GetSource(self.request_url, self.referrer_url)

    # Stored properties
    _illust = None
