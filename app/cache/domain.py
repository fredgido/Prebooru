from .. import db
class Domain(db.Model):
    __bind_key__ = 'cache'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    redirector = db.Column(db.Boolean, nullable=False)