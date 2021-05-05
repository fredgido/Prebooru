# WORKER.PY

# ## PYTHON IMPORTS
import os
import time
import atexit
import random
import threading
from apscheduler.schedulers.background import BackgroundScheduler

# ## LOCAL IMPORTS
from app import database as DB, app as APP
from app import session as SESSION
from app.models import Upload
from app.sources import base as BASE_SOURCE
from app.logical.utility import MinutesAgo, StaticVars
from app.logical.logger import LogError
from argparse import ArgumentParser


# ## GLOBAL VARIABLES

SCHED = None
SEM = threading.Semaphore()

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


def CheckPendingUploads():
    if SEM._value > 0 and Upload.query.filter_by(status="pending").count() > 0:
        ProcessUploads()


@StaticVars(processing=False)
def ProcessUploads():
    print("{ProcessUploads}")
    SEM.acquire()
    print("<semaphore acquire>")
    try:
        ProcessUploads.processing = True
        while True:
            uploads = Upload.query.filter_by(status="pending").all()
            for upload in uploads:
                if not ProcessUpload(upload):
                    break
            else:
                print("No pending uploads.")
                break
    finally:
        ProcessUploads.processing = False
        SEM.release()
        print("<semaphore release>")


def ProcessUpload(upload):
    print("ProcessUpload:\n",upload)
    try:
        BASE_SOURCE.ProcessUpload(upload)
        return True
    except Exception as e:
        print("\a\aCheckUploads: Exception occured in worker!\n", e)
        print("Unlocking the database...")
        SESSION.rollback()
        LogError('worker.CheckUploads', "Unhandled exception occurred on upload #%d: %s" % (upload.id, e))
        return False


def CheckSubscriptions():
    time.sleep(random.random() * 5)

def CheckGlobals():
    print(ProcessUploads.processing, SEM._value)

@APP.route('/check_uploads')
def check_uploads():
    if SEM._value > 0:
        SCHED.add_job(ProcessUploads)
        return "Begin processing uploads..."
    return "Uploads already processing!"

# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Worker to process uploads.")
    parser.add_argument('--logging', required=False, default=False, action="store_true", help="Display the SQL commands.")
    args = parser.parse_args()
    if args.logging:
        import logging
        logging.basicConfig()
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        SCHED = BackgroundScheduler(daemon=True)
        #SCHED.add_job(CheckSubscriptions, 'interval', seconds=15)
        SCHED.add_job(CheckPendingUploads, 'interval', minutes=5)
        SCHED.add_job(ExpireUploads, 'interval', minutes=1)
        #SCHED.add_job(CheckGlobals, 'interval', seconds=1)
        SCHED.add_job(ProcessUploads)
        SCHED.start()

    APP.run(threaded=True, port=4000)


    #while True:
    #    time.sleep(1)
