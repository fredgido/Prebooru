# APP/MODELS/POST.PY

# ##PYTHON IMPORTS
import datetime
from typing import List
from dataclasses import dataclass
from flask import url_for
from sqlalchemy.ext.associationproxy import association_proxy

# ##LOCAL IMPORTS
from .. import db, storage
from ..logical.utility import UniqueObjects
from .base import JsonModel, RemoveKeys
from .error import Error
from .illust_url import IllustUrl
from .notation import Notation
from .pool_element import PoolPost, pool_element_delete


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

PostNotations = db.Table(
    'post_notations',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'), primary_key=True),
    db.Column('notation_id', db.Integer, db.ForeignKey('notation.id'), primary_key=True),
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
    def file_path(self):
        return storage.DataDirectory('data', self.md5) + self.md5 + '.' + self.file_ext

    @property
    def sample_path(self):
        return storage.DataDirectory('sample', self.md5) + self.md5 + '.jpg' if storage.HasSample(self.width, self.height) or self.file_ext not in ['jpg', 'png', 'gif'] else self.file_path

    @property
    def preview_path(self):
        return storage.DataDirectory('preview', self.md5) + self.md5 + '.jpg' if storage.HasPreview(self.width, self.height) else self.file_path

    @property
    def show_url(self):
        return url_for("post.show_html", id=self.id)

    @property
    def illusts(self):
        return UniqueObjects([illust_url.illust for illust_url in self.illust_urls])

    @property
    def artists(self):
        return UniqueObjects([illust.artist for illust in self.illusts])

    @property
    def illust_ids(self):
        return list(set(illust_url.illust_id for illust_url in self.illust_urls))

    @property
    def artist_ids(self):
        return list(set(illust.artist_id for illust in self.illusts))

    id = db.Column(db.Integer, primary_key=True)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    file_ext = db.Column(db.String(6), nullable=False)
    md5 = db.Column(db.String(255), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    illust_urls = db.relationship(IllustUrl, secondary=PostIllustUrls, lazy='subquery', backref=db.backref('post', uselist=False, lazy=True), cascade='all,delete')
    errors = db.relationship(Error, secondary=PostErrors, lazy=True, cascade='all,delete')
    notations = db.relationship(Notation, secondary=PostNotations, lazy=True, backref=db.backref('posts', uselist=True, lazy=True), cascade='all,delete')
    _pools = db.relationship(PoolPost, backref='item', lazy=True, cascade='all,delete')
    pools = association_proxy('_pools', 'pool')
    created = db.Column(db.DateTime(timezone=False), nullable=False)

    def delete_pool(self, pool_id):
        pool_element_delete(pool_id, self)
