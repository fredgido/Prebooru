# APP/MODELS/POST.PY

# ##PYTHON IMPORTS
import datetime
from typing import List
from dataclasses import dataclass
from flask import url_for

# ##LOCAL IMPORTS
from .. import db, storage
from .base import JsonModel, RemoveKeys
from .illust_url import IllustUrl
from .error import Error


# ##GLOBAL VARIABLES

# Many-to-many tables

PostIllustUrls = db.Table(
    'post_illust_urls',
    db.Column('illust_url_id', db.Integer, db.ForeignKey('illust_url.id'), primary_key=True),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
)

PostErrors = db.Table(
    'post_errors',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('error_id', db.Integer, db.ForeignKey('error.id'), primary_key=True),
)


# Classes


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
        return storage.NetworkDirectory('data', self.md5) + self.md5 + '.' + self.file_ext

    @property
    def sample_url(self):
        return storage.NetworkDirectory('sample', self.md5) + self.md5 + '.jpg' if storage.HasSample(self.width, self.height) or self.file_ext not in ['jpg', 'png', 'gif'] else self.file_url

    @property
    def preview_url(self):
        return storage.NetworkDirectory('preview', self.md5) + self.md5 + '.jpg' if storage.HasPreview(self.width, self.height) else self.file_url

    @property
    def show_url(self):
        return url_for("post.show_html", id=self.id)

    id = db.Column(db.Integer, primary_key=True)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    file_ext = db.Column(db.String(6), nullable=False)
    md5 = db.Column(db.String(255), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    illust_urls = db.relationship(IllustUrl, secondary=PostIllustUrls, lazy='subquery', backref=db.backref('post', uselist=False, lazy=True), cascade='all,delete')
    errors = db.relationship(Error, secondary=PostErrors, lazy=True, cascade='all,delete')
    created = db.Column(db.DateTime(timezone=False), nullable=False)
