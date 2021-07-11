# APP/MODELS/ARTIST.PY

# ##PYTHON IMPORTS
import datetime
from typing import List
from dataclasses import dataclass
from flask import url_for
from sqlalchemy.orm import aliased
from sqlalchemy.ext.associationproxy import association_proxy

# ##LOCAL IMPORTS
from .. import DB
from ..sites import GetSiteDomain
from .base import JsonModel, RemoveKeys, DateTimeOrNull, IntOrNone, StrOrNone
from .artist import Artist
from .artist_url import ArtistUrl
from .illust import Illust
from .label import Label
from .description import Description
from .post import Post
from .illust_url import IllustUrl

# ##GLOBAL VARIABLES

BooruNames = DB.Table(
    'booru_names',
    DB.Column('label_id', DB.Integer, DB.ForeignKey('label.id'), primary_key=True),
    DB.Column('booru_id', DB.Integer, DB.ForeignKey('booru.id'), primary_key=True),
)

BooruArtists = DB.Table(
    'booru_artists',
    DB.Column('artist_id', DB.Integer, DB.ForeignKey('artist.id'), primary_key=True),
    DB.Column('booru_id', DB.Integer, DB.ForeignKey('booru.id'), primary_key=True),
)


@dataclass
class Booru(JsonModel):
    id: int
    danbooru_id: int
    current_name: str
    names: List[lambda x: x['name']]
    artist_ids: List
    created: datetime.datetime.isoformat
    updated: datetime.datetime.isoformat
    id = DB.Column(DB.Integer, primary_key=True)
    danbooru_id = DB.Column(DB.Integer, nullable=False)
    current_name = DB.Column(DB.String(255), nullable=False)
    names = DB.relationship(Label, secondary=BooruNames, lazy=True, backref=DB.backref('boorus', lazy=True))
    artists = DB.relationship(Artist, secondary=BooruArtists, backref='boorus', lazy=True)
    created = DB.Column(DB.DateTime(timezone=False), nullable=False)
    updated = DB.Column(DB.DateTime(timezone=False), nullable=False)

    artist_ids = association_proxy('artists', 'id')

    @property
    def recent_posts(self):
        if not hasattr(self, '_recent_posts'):
            q = Post.query
            q = q.join(IllustUrl, Post.illust_urls).join(Illust).join(Artist).join(Booru, Artist.boorus).filter(Booru.id == self.id)
            q = q.order_by(Post.id.desc())
            q = q.limit(10)
            self._recent_posts = q.all()
        return self._recent_posts

    @property
    def illust_count(self):
        return Illust.query.join(Artist, Illust.artist).join(Booru, Artist.boorus).filter(Booru.id == self.id).count()

    @property
    def illust_search(self):
        return url_for("illust.index_html", **{'search[artist][boorus][id]': self.id})

    def delete(self):
        self.names.clear()
        self.artists.clear()
        DB.session.delete(self)
        DB.session.commit()

    @staticmethod
    def searchable_attributes():
        basic_attributes = ['id', 'danbooru_id', 'current_name', 'names', 'created', 'updated']
        relation_attributes = ['names', 'artists']
        return basic_attributes + relation_attributes
