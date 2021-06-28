# PREBOORU.PY
import colorama

# ## LOCAL IMPORTS
from app import app
from app import controllers as controller
from argparse import ArgumentParser


# ### INITIALIZATION

colorama.init(autoreset=True)

app.register_blueprint(controller.illust.bp)
app.register_blueprint(controller.artist.bp)
app.register_blueprint(controller.upload.bp)
app.register_blueprint(controller.post.bp)
app.register_blueprint(controller.pool.bp)
app.register_blueprint(controller.notation.bp)
app.register_blueprint(controller.proxy.bp)
app.register_blueprint(controller.similarity.bp)


# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Sever to process network requests.")
    parser.add_argument('--extension', required=False, default=False, action="store_true", help="Enable Chrome extension.")
    args = parser.parse_args()
    if args.extension:
        from flask_flaskwork import Flaskwork
        Flaskwork(app)
    app.run(threaded=True)
