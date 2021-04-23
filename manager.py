from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

app = Flask(__name__)
app.config.from_mapping(
    SQLALCHEMY_DATABASE_URI = 'sqlite:///prebooru.db',
    SQLALCHEMY_ECHO = False,
    SECRET_KEY = '\xfb\x12\xdf\xa1@i\xd6>V\xc0\xbb\x8fp\x16#Z\x0b\x81\xeb\x16',
    DEBUG = True,
    SQLALCHEMY_TRACK_MODIFICATIONS = False,
) 

db = SQLAlchemy(app)
migrate = Migrate(app, db, render_as_batch=True)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

import app.database as DB
DB.models.InitializeModels(db)

if __name__ == '__main__':
    manager.run()