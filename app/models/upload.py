# APP/MODELS/UPLOAD.PY

# ##PYTHON IMPORTS
import datetime
from typing import List
from dataclasses import dataclass
from flask import url_for

# ##LOCAL IMPORTS
from .. import DB
from ..logical.utility import UniqueObjects
from ..base_model import JsonModel, IntOrNone, StrOrNone
from .upload_url import UploadUrl
from .post import Post
from .error import Error

# ##GLOBAL VARIABLES

# Many-to-many tables

UploadUrls = DB.Table(
    'upload_urls',
    DB.Column('upload_id', DB.Integer, DB.ForeignKey('upload.id'), primary_key=True),
    DB.Column('upload_url_id', DB.Integer, DB.ForeignKey('upload_url.id'), primary_key=True),
)
UploadErrors = DB.Table(
    'upload_errors',
    DB.Column('upload_id', DB.Integer, DB.ForeignKey('upload.id'), primary_key=True),
    DB.Column('error_id', DB.Integer, DB.ForeignKey('error.id'), primary_key=True),
)
UploadPosts = DB.Table(
    'upload_posts',
    DB.Column('upload_id', DB.Integer, DB.ForeignKey('upload.id'), primary_key=True),
    DB.Column('post_id', DB.Integer, DB.ForeignKey('post.id'), primary_key=True),
)


# Classes


@dataclass
class Upload(JsonModel):
    id: int
    subscription_id: IntOrNone
    request_url: StrOrNone
    media_filepath: StrOrNone
    sample_filepath: StrOrNone
    illust_url_id: IntOrNone
    type: str
    status: str
    successes: int
    failures: int
    image_urls: List
    post_ids: lambda x: x
    errors: List
    created: datetime.datetime.isoformat

    id = DB.Column(DB.Integer, primary_key=True)
    request_url = DB.Column(DB.String(255), nullable=True)
    successes = DB.Column(DB.Integer, nullable=False)
    failures = DB.Column(DB.Integer, nullable=False)
    type = DB.Column(DB.String(255), nullable=False)
    status = DB.Column(DB.String(255), nullable=False)
    media_filepath = DB.Column(DB.String(255), nullable=True)
    sample_filepath = DB.Column(DB.String(255), nullable=True)
    illust_url_id = DB.Column(DB.Integer, DB.ForeignKey('illust_url.id'), nullable=True)
    subscription_id = DB.Column(DB.Integer, DB.ForeignKey('subscription.id'), nullable=True)
    image_urls = DB.relationship(UploadUrl, secondary=UploadUrls, lazy='subquery', uselist=True, backref=DB.backref('upload', lazy=True, uselist=False), cascade='all,delete')
    posts = DB.relationship(Post, secondary=UploadPosts, backref=DB.backref('uploads', lazy=True), lazy=True)
    errors = DB.relationship(Error, secondary=UploadErrors, lazy=True, cascade='all,delete')
    created = DB.Column(DB.DateTime(timezone=False), nullable=False)

    @property
    def post_ids(self):
        return [post.id for post in self.posts]

    @property
    def show_url(self):
        return url_for("upload.show_html", id=self.id)

    @property
    def site_id(self):
        return self._source.SITE_ID

    @property
    def site_illust_id(self):
        if self.request_url:
            return self._source.GetIllustId(self.request_url)
        elif self.illust_url.id:
            return self.illust_url.illust.site_illust_id
        raise Exception("Unable to find site illust ID for upload #%d" % self.id)

    @property
    def illust(self):
        if self._illust is None:
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
        from ..sources.base_source import GetPostSource, GetSourceById
        if self.request_url:
            return GetPostSource(self.request_url)
        elif self.illust_url_id:
            return GetSourceById(self.illust_url.site_id)
        raise Exception("Unable to find source for upload #%d" % self.id)

    # Stored properties
    _illust = None

    @staticmethod
    def searchable_attributes():
        basic_attributes = ['id', 'successes', 'failures', 'subscription_id', 'illust_url_id', 'request_url', 'type', 'status', 'media_filepath', 'sample_filepath', 'created']
        relation_attributes = ['image_urls', 'posts', 'errors']
        return basic_attributes + relation_attributes
