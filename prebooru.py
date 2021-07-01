# PREBOORU.PY

# ## PYTHON IMPORTS
from argparse import ArgumentParser
import colorama

# ## LOCAL IMPORTS
from app import PREBOORU_APP
from app import controllers as controller


# ### INITIALIZATION

colorama.init(autoreset=True)

PREBOORU_APP.register_blueprint(controller.illust.bp)
PREBOORU_APP.register_blueprint(controller.artist.bp)
PREBOORU_APP.register_blueprint(controller.booru.bp)
PREBOORU_APP.register_blueprint(controller.upload.bp)
PREBOORU_APP.register_blueprint(controller.post.bp)
PREBOORU_APP.register_blueprint(controller.pool.bp)
PREBOORU_APP.register_blueprint(controller.notation.bp)
PREBOORU_APP.register_blueprint(controller.proxy.bp)
PREBOORU_APP.register_blueprint(controller.similarity.bp)


# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Server to process network requests.")
    parser.add_argument('--extension', required=False, default=False, action="store_true", help="Enable Chrome extension.")
    args = parser.parse_args()
    if args.extension:
        from flask_flaskwork import Flaskwork
        Flaskwork(PREBOORU_APP)
    PREBOORU_APP.run(threaded=True)
