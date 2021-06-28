# WORKER.PY

# ## PYTHON IMPORTS
import os
import time
from flask import request
import atexit
import random
import requests
import threading
from apscheduler.schedulers.background import BackgroundScheduler

# ## LOCAL IMPORTS
from app import database as DB, app as APP
from app import session as SESSION
from app.cache import ApiData, MediaFile
from app.models import Upload, Illust, Artist
from app.sources import base as BASE_SOURCE
from app.logical.utility import MinutesAgo, StaticVars, GetCurrentTime
from app.logical.logger import LogError
#from app.logical.unshortenlink import UnshortenAllLinks
from argparse import ArgumentParser


# ## GLOBAL VARIABLES

SCHED = None
SEM = threading.Semaphore()

# ### FUNCTIONS

#print(APP)

@atexit.register
def Cleanup():
    if SCHED is not None and SCHED.running:
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


def CheckForShortLinks():
    print("CheckForShortLinks")
    UnshortenAllLinks()


@StaticVars(processing=False)
def ProcessUploads():
    print("{ProcessUploads}")
    SEM.acquire()
    print("<semaphore acquire>")
    try:
        ProcessUploads.processing = True
        post_ids = []
        while True:
            uploads = Upload.query.filter_by(status="pending").all()
            for upload in uploads:
                if not ProcessUpload(upload):
                    break
                post_ids.extend(upload.post_ids)
            else:
                print("No pending uploads.")
                break
            # Give time for upload creation transactions to complete
            time.sleep(5)
        if len(post_ids):
            print("Check to see if the similarity server call will work.")
            try:
                requests.get('http://127.0.0.1:3000/check_posts',timeout=2)
            except Exception as e:
                print("Unable to contact similarity server:", e)
    finally:
        ProcessUploads.processing = False
        SEM.release()
        print("<semaphore release>")


def ProcessUpload(upload):
    #print("ProcessUpload:\n",upload)
    try:
        BASE_SOURCE.ProcessUpload(upload)
        return True
    except Exception as e:
        print("\a\aProcessUpload: Exception occured in worker!\n", e)
        print("Unlocking the database...")
        SESSION.rollback()
        LogError('worker.ProcessUpload', "Unhandled exception occurred on upload #%d: %s" % (upload.id, e))
        return False

def ProcessArtist(artist):
    SESSION.add(artist)
    print("ProcessArtist:\n",artist.id)
    try:
        BASE_SOURCE.ProcessArtist(artist)
        return True
    except Exception as e:
        print("\a\aProcessArtist: Exception occured in worker!\n", e)
        print("Unlocking the database...")
        SESSION.rollback()
        LogError('worker.ProcessArtist', "Unhandled exception occurred on artist #%d: %s" % (artist.id, e))
        return False

def CreateNewArtist(site_id, site_artist_id):
    try:
        BASE_SOURCE.CreateNewArtist(site_id, site_artist_id)
        return True
    except Exception as e:
        print("\a\aCreateNewArtist: Exception occured in worker!\n", e)
        print("Unlocking the database...")
        SESSION.rollback()
        LogError('worker.CreateNewArtist', "Unhandled exception occurred creating new artist (%d - %d): %s" % (site_id, site_artist_id, e))
        return False

def ProcessIllust(illust):
    print("ProcessIllust:\n",illust.id)
    try:
        BASE_SOURCE.ProcessIllust(illust)
        return True
    except Exception as e:
        print("\a\aProcessIllust: Exception occured in worker!\n", e)
        print("Unlocking the database...")
        SESSION.rollback()
        LogError('worker.ProcessIllust', "Unhandled exception occurred on illust #%d: %s" % (illust.id, e))
        return False

def CheckSubscriptions():
    time.sleep(random.random() * 5)

def ExpungeCacheRecords():
    print("ExpungeCacheRecords")
    SEM.acquire()
    print("<semaphore acquire>")
    api_delete_count = ApiData.query.filter(ApiData.expires < GetCurrentTime()).count()
    print("Records to delete:", api_delete_count)
    if api_delete_count > 0:
        ApiData.query.filter(ApiData.expires < GetCurrentTime()).delete()
        SESSION.commit()
    media_delete_count = MediaFile.query.filter(MediaFile.expires < GetCurrentTime()).count()
    print("Media files to delete:", media_delete_count)
    if media_delete_count > 0:
        media_records = MediaFile.query.filter(MediaFile.expires < GetCurrentTime()).all()
        for media in media_records:
            if os.path.exists(media.file_path):
                os.remove(media.file_path)
                time.sleep(0.2)
            SESSION.delete(media)
        SESSION.commit()
    SEM.release()
    print("<semaphore release>")

def CheckGlobals():
    print(ProcessUploads.processing, SEM._value)

@APP.route('/check_uploads')
def check_uploads():
    if SEM._value > 0:
        SCHED.add_job(ProcessUploads)
        return "Begin processing uploads..."
    return "Uploads already processing!"

@APP.route('/requery_artist/<int:id>')
def requery_artist(id):
    artist = Artist.query.filter_by(id=id).first()
    if artist is None:
        return "Artist #%d not found!" % id
    SCHED.add_job(ProcessArtist, args=[artist])
    return "Reprocessing artist #%d" % id

@APP.route('/create_artist')
def create_artist():
    if 'site_id' not in request.values or 'artist_id' not in request.values:
        return "Must include site ID and artist ID."
    site_id = int(request.values['site_id'])
    artist_id = int(request.values['artist_id'])
    artist = Artist.query.filter_by(site_artist_id=artist_id, site_id=site_id).first()
    if artist is not None:
        return "Record already created on artist #%d" % artist.id
    SCHED.add_job(CreateNewArtist, args=[site_id, artist_id])
    return "Creating new artist..."

@APP.route('/requery_illust')
def requery_illust():
    pass

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
        ExpungeCacheRecords()
        SCHED = BackgroundScheduler(daemon=True)
        #SCHED.add_job(CheckSubscriptions, 'interval', seconds=15)
        SCHED.add_job(CheckPendingUploads, 'interval', minutes=5)
        SCHED.add_job(ExpireUploads, 'interval', minutes=1)
        #SCHED.add_job(CheckGlobals, 'interval', seconds=1)
        SCHED.add_job(ExpungeCacheRecords, 'interval', hours=1)
        #SCHED.add_job(CheckForShortLinks, 'interval', hours=2)
        SCHED.add_job(ProcessUploads)
        SCHED.start()

    APP.run(threaded=True, port=4000)


    #while True:
    #    time.sleep(1)
