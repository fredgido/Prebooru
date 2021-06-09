# PREBOORU.PY

# ## LOCAL IMPORTS
from app import app
from app.controllers import uploads, posts, illusts, artists, pools
from argparse import ArgumentParser


# ### INITIALIZATION

app.register_blueprint(illusts.bp)
app.register_blueprint(artists.bp)
app.register_blueprint(uploads.bp)
app.register_blueprint(posts.bp)
app.register_blueprint(pools.bp)


# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Sever to process network requests.")
    parser.add_argument('--extension', required=False, default=False, action="store_true", help="Enable Chrome extension.")
    args = parser.parse_args()
    if args.extension:
        from flask_flaskwork import Flaskwork
        Flaskwork(app)
    app.run(threaded=True)
