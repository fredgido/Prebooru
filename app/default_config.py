# APP/DEFAULT_CONFIG.PY

# ## DIRECTORY VARIABLES

"""Filepaths need to end with a double backslash ('\\')"""
import os

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

"""All backslashes ('\') in a filepath need to be double escaped ('\\')"""

WORKING_DIRECTORY = os.environ.get('WORKING_DIRECTORY', "C:\\Temp\\")
DATA_FILEPATH = os.environ.get('DATA_FILEPATH', "data\\")
IMAGE_FILEPATH = os.environ.get('IMAGE_FILEPATH', "pictures\\")

# ## DATABASE VARIABLES

# Relative path to the DB file
DB_PATH = os.environ.get('DB_PATH', r'db\prebooru.db')
CACHE_PATH = r'db\cache.db'
SIMILARITY_PATH = r'db\similarity.db'

# SCHEDULER
SCHEDULER_JOBSTORES = {"default": SQLAlchemyJobStore(url=os.environ.get('SCHEDULER_JOBSTORES', r"sqlite:///db\jobs.db"))}

SCHEDULER_EXECUTORS = {
    "default": {"type": "processpool", "max_workers": 5},
    'threadpool': {'type': 'threadpool', 'max_workers': 20}
}

SCHEDULER_JOB_DEFAULTS = {"coalesce": False, "max_instances": 4}

SCHEDULER_API_ENABLED = True

# ## NETWORK VARIABLES

DANBOORU_HOSTNAME = 'https://danbooru.donmai.us'

DANBOORU_USERNAME = None
DANBOORU_APIKEY = None

# Log into Pixiv and get this value from the cookie PHPSESSID
PIXIV_PHPSESSID = os.environ.get('PIXIV_PHPSESSID')
print(PIXIV_PHPSESSID)

PREBOORU_PORT = int(os.environ.get('PREBOORU_PORT', 5000))
WORKER_PORT = 4000
SIMILARITY_PORT = 3000
IMAGE_PORT = 1234

HAS_EXTERNAL_IMAGE_SERVER = False

# ## OTHER VARIABLES

VERSION = '1.2.1'
DEBUG_MODE = False
