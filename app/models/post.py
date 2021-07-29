# APP/MODELS/POST.PY

# ##PYTHON IMPORTS
import itertools
import datetime
from types import SimpleNamespace
from typing import List
from dataclasses import dataclass
from flask import url_for
from sqlalchemy.orm import lazyload
from sqlalchemy.ext.associationproxy import association_proxy

# ##LOCAL IMPORTS
from .. import DB, storage
from ..logical.utility import UniqueObjects
from .base import JsonModel, RemoveKeys
from .error import Error
from .illust_url import IllustUrl
from .notation import Notation
from .pool_element import PoolPost, pool_element_delete
from ..similarity import SimilarityPool

# ##GLOBAL VARIABLES

# Many-to-many tables

PostIllustUrls = DB.Table(
    'post_illust_urls',
    DB.Column('illust_url_id', DB.Integer, DB.ForeignKey('illust_url.id'), primary_key=True),
    DB.Column('post_id', DB.Integer, DB.ForeignKey('post.id'), primary_key=True),
)

PostErrors = DB.Table(
    'post_errors',
    DB.Column('post_id', DB.Integer, DB.ForeignKey('post.id'), primary_key=True),
    DB.Column('error_id', DB.Integer, DB.ForeignKey('error.id'), primary_key=True),
)

PostNotations = DB.Table(
    'post_notations',
    DB.Column('post_id', DB.Integer, DB.ForeignKey('post.id'), primary_key=True),
    DB.Column('notation_id', DB.Integer, DB.ForeignKey('notation.id'), primary_key=True),
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
    def related_posts(self):
        illust_posts = [illust.posts for illust in self.illusts]
        post_generator = (post for post in itertools.chain(*illust_posts) if post is not None)
        return [post for post in UniqueObjects(post_generator) if post.id != self.id]

    @property
    def illusts(self):
        return UniqueObjects([illust_url.illust for illust_url in self.illust_urls])

    @property
    def artists(self):
        return UniqueObjects([illust.artist for illust in self.illusts])

    @property
    def boorus(self):
        return UniqueObjects(list(itertools.chain(*[artist.boorus for artist in self.artists])))

    @property
    def illust_ids(self):
        return list(set(illust_url.illust_id for illust_url in self.illust_urls))

    @property
    def artist_ids(self):
        return list(set(illust.artist_id for illust in self.illusts))

    @property
    def similar_pool_id(self):
        if not hasattr(self, '_similar_pool_id'):
            self.similar_posts
        return self._similar_pool_id

    @property
    def similar_post_count(self):
        if not hasattr(self, '_similar_post_count'):
            self.similar_posts
        return self._similar_post_count

    @property
    def similar_posts(self):
        if not hasattr(self, '_similar_posts'):
            setattr(self, '_similar_posts', [])
            pool = SimilarityPool.query.filter_by(post_id=self.id).first()
            setattr(self, '_similar_pool_id', pool.id if pool is not None else None)
            if pool is None or len(pool.elements) == 0:
                setattr(self, '_similar_post_count', 0)
                return self._similar_posts
            setattr(self, '_similar_post_count', len(pool.elements))
            sorted_elements = sorted(pool.elements, key=lambda x: x.score, reverse=True)[:10]
            similar_post_ids = [element.post_id for element in sorted_elements]
            similar_posts = Post.query.options(lazyload('*')).filter(Post.id.in_(similar_post_ids))
            for element in sorted_elements:
                data = SimpleNamespace(element=element, pool=pool, post=None)
                data.post = next(filter(lambda x: x.id == element.post_id, similar_posts), None)
                self._similar_posts.append(data)
        return self._similar_posts

    id = DB.Column(DB.Integer, primary_key=True)
    width = DB.Column(DB.Integer, nullable=False)
    height = DB.Column(DB.Integer, nullable=False)
    file_ext = DB.Column(DB.String(6), nullable=False)
    md5 = DB.Column(DB.String(255), nullable=False)
    size = DB.Column(DB.Integer, nullable=False)
    illust_urls = DB.relationship(IllustUrl, secondary=PostIllustUrls, lazy='subquery', backref=DB.backref('post', uselist=False, lazy=True))
    errors = DB.relationship(Error, secondary=PostErrors, lazy=True, cascade='all,delete')
    notations = DB.relationship(Notation, secondary=PostNotations, lazy=True, backref=DB.backref('post', uselist=False, lazy=True), cascade='all,delete')
    _pools = DB.relationship(PoolPost, backref='item', lazy=True, cascade='all,delete')
    pools = association_proxy('_pools', 'pool')
    created = DB.Column(DB.DateTime(timezone=False), nullable=False)

    def delete_pool(self, pool_id):
        pool_element_delete(pool_id, self)

    def delete(self):
        pools = [pool for pool in self.pools]
        # self.uploads.clear()
        DB.session.delete(self)
        DB.session.commit()
        if len(pools) > 0:
            for pool in pools:
                pool._elements.reorder()
            DB.session.commit()

    @staticmethod
    def searchable_attributes():
        basic_attributes = ['id', 'width', 'height', 'size', 'file_ext', 'md5', 'created']
        relation_attributes = ['illust_urls', 'notations', 'errors']
        return basic_attributes + relation_attributes
