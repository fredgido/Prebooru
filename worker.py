# WORKER.PY

# ## PYTHON IMPORTS
import time
import atexit
import random
import datetime
from apscheduler.schedulers.background import BackgroundScheduler

# ## LOCAL IMPORTS
from app import database as DB
from app import session as SESSION
from app.models import Upload, Subscription
from app.sources import base as BASE_SOURCE
from app.logical.utility import MinutesAgo

# ### FUNCTIONS

@atexit.register
def Cleanup():
    if sched is not None:
        sched.shutdown()

def ExpireUploads():
    time.sleep(random.random() * 5)
    print("ExpireUploads")
    expired_uploads = Upload.query.filter(Upload.created < MinutesAgo(5)).filter_by(status="processing").all()
    if len(expired_uploads):
        print("Found %d uploads to expire!" % len(expired_uploads))
    for upload in expired_uploads:
        upload.status = "complete"
        DB.local.CreateAndAppendError('worker.CheckUploads', "Upload has expired.", upload)

def CheckUploads():
    print("CheckUploads")
    upload = Upload.query.filter_by(status="pending").first()
    print(upload)
    if upload is None:
        return
    try:
        BASE_SOURCE.ProcessUpload(upload)
    except Exception as e:
        print("CheckUploads: Exception occured in worker!\n", e)
        print("Unlocking the database...")
        SESSION.rollback()
        raise


def CheckSubscriptions():
    time.sleep(random.random() * 5)
    #print("CheckSubscriptions")
    #print(Subscription.query.all())


# ##EXECUTION START

if __name__ == '__main__':
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(CheckUploads, 'interval', seconds=5)
    sched.add_job(CheckSubscriptions, 'interval', seconds=15)
    sched.add_job(ExpireUploads, 'interval', minutes=1)
    sched.start()
    while True:
        time.sleep(1)
