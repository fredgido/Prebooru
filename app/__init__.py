from .config import DB_PATH
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask("prebooru")  # See if I can rename this
app.config.from_mapping(
    SQLALCHEMY_DATABASE_URI='sqlite:///%s' % DB_PATH,
    SQLALCHEMY_ECHO=False,
    SECRET_KEY='\xfb\x12\xdf\xa1@i\xd6>V\xc0\xbb\x8fp\x16#Z\x0b\x81\xeb\x16',
    DEBUG=True,
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)

db = SQLAlchemy(app)

session = db.session
