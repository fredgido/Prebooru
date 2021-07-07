# PREBOORU.PY

# ## PYTHON IMPORTS
from argparse import ArgumentParser
import colorama

# ## LOCAL IMPORTS
from app import PREBOORU_APP
from app import controllers
from app import helpers

# ### INITIALIZATION

colorama.init(autoreset=True)

PREBOORU_APP.register_blueprint(controllers.illust.bp)
PREBOORU_APP.register_blueprint(controllers.illust_url.bp)
PREBOORU_APP.register_blueprint(controllers.artist.bp)
PREBOORU_APP.register_blueprint(controllers.booru.bp)
PREBOORU_APP.register_blueprint(controllers.upload.bp)
PREBOORU_APP.register_blueprint(controllers.post.bp)
PREBOORU_APP.register_blueprint(controllers.pool.bp)
PREBOORU_APP.register_blueprint(controllers.pool_element.bp)
PREBOORU_APP.register_blueprint(controllers.notation.bp)
PREBOORU_APP.register_blueprint(controllers.proxy.bp)
PREBOORU_APP.register_blueprint(controllers.similarity.bp)

PREBOORU_APP.jinja_env.globals.update(helpers=helpers)

# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Server to process network requests.")
    parser.add_argument('--extension', required=False, default=False, action="store_true", help="Enable Chrome extension.")
    args = parser.parse_args()
    if args.extension:
        from flask_flaskwork import Flaskwork
        Flaskwork(PREBOORU_APP)
    PREBOORU_APP.run(threaded=True)
