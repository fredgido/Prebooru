# WORKER.PY

# ## PYTHON IMPORTS
import time
import atexit
import random
from apscheduler.schedulers.background import BackgroundScheduler

# ## LOCAL IMPORTS
from app.models import Upload, Subscription
from app.sources import base as BASE_SOURCE


# ### FUNCTIONS

@atexit.register
def Cleanup():
    if sched is not None:
        sched.shutdown()


def CheckUploads():
    print("CheckUploads")
    upload = Upload.query.filter_by(status="pending").first()
    print(upload)
    if upload is not None:
        BASE_SOURCE.ProcessUpload(upload)


def CheckSubscriptions():
    time.sleep(random.random() * 5)
    print("CheckSubscriptions")
    print(Subscription.query.all())


# ##EXECUTION START

if __name__ == '__main__':
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(CheckUploads, 'interval', seconds=5)
    sched.add_job(CheckSubscriptions, 'interval', seconds=15)
    sched.start()
    while True:
        time.sleep(1)
