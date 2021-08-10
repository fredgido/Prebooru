# PREBOORU.PY

# ## PYTHON IMPORTS
import os
import atexit
import colorama
from argparse import ArgumentParser

# ## LOCAL IMPORTS
from app import PREBOORU_APP
from app import controllers
from app import helpers
from app.logical.file import LoadDefault, PutGetJSON
from app.config import WORKING_DIRECTORY, DATA_FILEPATH

# ## GLOBAL VARIABLES

SERVER_PID_FILE = WORKING_DIRECTORY + DATA_FILEPATH + 'prebooru-server-pid.json'
SERVER_PID = next(iter(LoadDefault(SERVER_PID_FILE, [])), None)


# ## FUNCTIONS

@atexit.register
def Cleanup():
    if SERVER_PID is not None:
        PutGetJSON(SERVER_PID_FILE, 'w', [])


def Main(args):
    global SERVER_PID
    if SERVER_PID is not None:
        print("Server process already running: %d" % SERVER_PID)
        input()
        exit(-1)
    if args.extension:
        from flask_flaskwork import Flaskwork
        Flaskwork(PREBOORU_APP)
    if args.title:
        os.system('title Prebooru Server')
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        SERVER_PID = os.getpid()
        PutGetJSON(SERVER_PID_FILE, 'w', [SERVER_PID])
    PREBOORU_APP.run(threaded=True)


# ### INITIALIZATION

colorama.init(autoreset=True)

PREBOORU_APP.register_blueprint(controllers.illust.bp)
PREBOORU_APP.register_blueprint(controllers.illust_url.bp)
PREBOORU_APP.register_blueprint(controllers.artist.bp)
PREBOORU_APP.register_blueprint(controllers.artist_url.bp)
PREBOORU_APP.register_blueprint(controllers.booru.bp)
PREBOORU_APP.register_blueprint(controllers.upload.bp)
PREBOORU_APP.register_blueprint(controllers.post.bp)
PREBOORU_APP.register_blueprint(controllers.pool.bp)
PREBOORU_APP.register_blueprint(controllers.pool_element.bp)
PREBOORU_APP.register_blueprint(controllers.tag.bp)
PREBOORU_APP.register_blueprint(controllers.notation.bp)
PREBOORU_APP.register_blueprint(controllers.error.bp)
PREBOORU_APP.register_blueprint(controllers.proxy.bp)
PREBOORU_APP.register_blueprint(controllers.static.bp)
PREBOORU_APP.register_blueprint(controllers.similarity.bp)
PREBOORU_APP.register_blueprint(controllers.similarity_pool.bp)
PREBOORU_APP.register_blueprint(controllers.similarity_pool_element.bp)

PREBOORU_APP.jinja_env.globals.update(helpers=helpers)
PREBOORU_APP.jinja_env.add_extension('jinja2.ext.do')
PREBOORU_APP.jinja_env.add_extension('jinja2.ext.loopcontrols')

# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Server to process network requests.")
    parser.add_argument('--extension', required=False, default=False, action="store_true", help="Enable Chrome extension.")
    parser.add_argument('--title', required=False, default=False, action="store_true", help="Adds server title to console window.")
    args = parser.parse_args()
    Main(args)
