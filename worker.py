# WORKER.PY

# ## PYTHON IMPORTS
import time
import atexit
import random
from apscheduler.schedulers.background import BackgroundScheduler

# ## LOCAL IMPORTS
from app import database as DB
from app import session as SESSION
from app.models import Upload
from app.sources import base as BASE_SOURCE
from app.logical.utility import MinutesAgo
from app.logical.logger import LogError
from argparse import ArgumentParser


# ## GLOBAL VARIABLES

SCHED = None


# ### FUNCTIONS


@atexit.register
def Cleanup():
    if SCHED is not None:
        SCHED.shutdown()


def ExpireUploads():
    time.sleep(random.random() * 5)
    print("ExpireUploads")
    expired_uploads = Upload.query.filter(Upload.created < MinutesAgo(5)).filter_by(status="processing").all()
    if len(expired_uploads):
        print("Found %d uploads to expire!" % len(expired_uploads))
    for upload in expired_uploads:
        upload.status = "complete"
        DB.local.CreateAndAppendError('worker.ExpireUploads', "Upload has expired.", upload)


def CheckUploads():
    print("CheckUploads")

    upload = Upload.query.filter_by(status="pending").first()
    print(upload)
    if upload is None:
        return
    try:
        BASE_SOURCE.ProcessUpload(upload)
    except Exception as e:
        print("\a\aCheckUploads: Exception occured in worker!\n", e)
        print("Unlocking the database...")
        SESSION.rollback()
        LogError('worker.CheckUploads', "Unhandled exception occurred on upload #%d: %s" % (upload.id, e))


def CheckSubscriptions():
    time.sleep(random.random() * 5)


# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Worker to process uploads.")
    parser.add_argument('--logging', required=False, default=False, action="store_true", help="Display the SQL commands.")
    args = parser.parse_args()
    if args.logging:
        import logging
        logging.basicConfig()
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    SCHED = BackgroundScheduler(daemon=True)
    SCHED.add_job(CheckUploads, 'interval', seconds=5)
    SCHED.add_job(CheckSubscriptions, 'interval', seconds=15)
    SCHED.add_job(ExpireUploads, 'interval', minutes=1)
    SCHED.start()
    while True:
        time.sleep(1)
