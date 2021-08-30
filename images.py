# IMAGES.PY

# ## PYTHON IMPORTS
import os
import atexit
from argparse import ArgumentParser
from flask import Flask, request, send_from_directory

# ## LOCAL IMPORTS
from app.logical.file import LoadDefault, PutGetJSON
from app.storage import IMAGE_DIRECTORY
from app.config import WORKING_DIRECTORY, DATA_FILEPATH, IMAGE_PORT


# ## GLOBAL VARIABLES

SERVER_PID_FILE = WORKING_DIRECTORY + DATA_FILEPATH + 'image-server-pid.json'
SERVER_PID = next(iter(LoadDefault(SERVER_PID_FILE, [])), None)

IMAGES_APP = Flask(__name__)
IMAGES_APP.config.from_mapping(
    DEBUG=True,
)


# ## FUNCTIONS

# #### Route functions

@IMAGES_APP.route('/<path:path>')
def send_file(path):
    return send_from_directory(IMAGE_DIRECTORY, path)


# #### Initialization functions

@atexit.register
def Cleanup():
    if SERVER_PID is not None:
        PutGetJSON(SERVER_PID_FILE, 'w', [])


# #### Main execution functions

def StartServer(args):
    if args.title:
        os.system('title Image Server')
    global SERVER_PID
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        SERVER_PID = os.getpid()
        PutGetJSON(SERVER_PID_FILE, 'w', [SERVER_PID])
    IMAGES_APP.run(threaded=True, port=2345) # IMAGE_PORT


# ## EXECUTION START

if __name__ == "__main__":
    parser = ArgumentParser(description="Worker to process uploads.")
    parser.add_argument('--title', required=False, default=False, action="store_true", help="Adds server title to console window.")
    args = parser.parse_args()
    StartServer(args)
