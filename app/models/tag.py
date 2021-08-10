# APP/MODELS/TAG.PY

# ##PYTHON IMPORTS
from dataclasses import dataclass

# ##LOCAL IMPORTS
from .. import DB
from ..base_model import JsonModel


# ##GLOBAL VARIABLES


@dataclass
class Tag(JsonModel):
    id: int
    name: str
    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.Unicode(255), nullable=False)

    @property
    def recent_posts(self):
        from .post import Post
        if not hasattr(self, '_recent_posts'):
            q = self._post_query
            q = q.order_by(Post.id.desc())
            q = q.limit(10)
            self._recent_posts = q.all()
        return self._recent_posts

    @property
    def illust_count(self):
        return self._illust_query.get_count()

    @property
    def post_count(self):
        return self._post_query.get_count()

    @property
    def _illust_query(self):
        from .illust import Illust
        return Illust.query.join(Tag, Illust.tags).filter(Tag.id == self.id)

    @property
    def _post_query(self):
        from .post import Post
        from .illust_url import IllustUrl
        from .illust import Illust
        return Post.query.join(IllustUrl, Post.illust_urls).join(Illust).join(Tag, Illust.tags).filter(Tag.id == self.id)

    @staticmethod
    def searchable_attributes():
        return ['id', 'name']
