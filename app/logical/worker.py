import itertools
import os
import time

from sqlalchemy import not_
from sqlalchemy.orm import Session

from app import SESSION, database, DB
from app.database.artist_db import UpdateArtistFromSource
from app.database.booru_db import CreateBooruFromParameters, BooruAppendArtist
from app.database.error_db import AppendError, CreateAndAppendError
from app.database.illust_db import CreateIllustFromSource, UpdateIllustFromSource
from app.database.upload_db import SetUploadStatus, IsDuplicate
from app.downloader.file_downloader import ConvertFileUpload
from app.downloader.network_downloader import ConvertNetworkUpload
from app.logical.check_booru_posts import CheckPostsForDanbooruID
from app.logical.file import PutGetJSON
from app.logical.logger import LogError
from app.logical.utility import GetCurrentTime, MinutesAgo
from app.models import Upload, Illust, Artist, Booru, ApiData, MediaFile
from app.sources.base_source import GetPostSource, GetSourceById
from app.sources.danbooru_source import GetArtistsByMultipleUrls
from app.config import WORKING_DIRECTORY, DATA_FILEPATH, WORKER_PORT, DEBUG_MODE, VERSION

READ_ENGINE = DB.engine.execution_options(isolation_level="READ UNCOMMITTED")


BOORU_ARTISTS_FILE = WORKING_DIRECTORY + DATA_FILEPATH + 'booru_artists_file.json'

# #### Helper functions

def CheckRequery(instance):
    return instance.requery is None or instance.requery < GetCurrentTime()


def GetPendingUploadIDs():
    # Doing this because there were issues with subsequent iterations of the
    # while loop in ProcessUploads not registering newly created uploads.
    with Session(bind=READ_ENGINE) as session:
        return [upload.id for upload in session.query(Upload).filter_by(status="pending").all()]


def GetUploadWait(upload_id):
    for i in range(3):
        upload = Upload.find(upload_id)
        if upload is not None:
            return upload
        time.sleep(0.5)


def SaveLastCheckArtistId(max_artist_id):
    BOORU_ARTISTS_DATA['last_checked_artist_id'] = max_artist_id
    PutGetJSON(BOORU_ARTISTS_FILE, 'w', BOORU_ARTISTS_DATA)


def LoadBooruArtistData():
    global BOORU_ARTISTS_DATA
    if BOORU_ARTISTS_DATA is None:
        BOORU_ARTISTS_DATA = PutGetJSON(BOORU_ARTISTS_FILE, 'r')
        BOORU_ARTISTS_DATA = BOORU_ARTISTS_DATA if type(BOORU_ARTISTS_DATA) is dict else {}
        BOORU_ARTISTS_DATA['last_checked_artist_id'] = BOORU_ARTISTS_DATA['last_checked_artist_id'] if ('last_checked_artist_id' in BOORU_ARTISTS_DATA) and (type(BOORU_ARTISTS_DATA['last_checked_artist_id']) is int) else 0


# #### Upload functions

def ProcessUploadWrap(upload):
    try:
        ProcessUpload(upload)
        return True
    except Exception as e:
        print("\a\aProcessUpload: Exception occured in worker!\n", e)
        print("Unlocking the database...")
        SESSION.rollback()
        LogError('worker.ProcessUpload', "Unhandled exception occurred on upload #%d: %s" % (upload.id, e))
        SetUploadStatus(upload, 'error')
        return False


def ProcessUpload(upload):
    SetUploadStatus(upload, 'processing')
    if upload.type == 'post':
        ProcessNetworkUpload(upload)
    elif upload.type == 'file':
        ProcessFileUpload(upload)


def ProcessNetworkUpload(upload):
    # Request URL should have already been validated, so no null test needed
    source = GetPostSource(upload.request_url)
    site_illust_id = source.GetIllustId(upload.request_url)
    site_id = source.SITE_ID
    error = source.Prework(site_illust_id)
    if error is not None:
        AppendError(upload, error)
    illust = Illust.query.filter_by(site_id=site_id, site_illust_id=site_illust_id).first()
    if illust is None:
        illust = CreateIllustFromSource(site_illust_id, source)
        if illust is None:
            SetUploadStatus(upload, 'error')
            CreateAndAppendError('worker.ProcessNetworkUpload',
                                 "Unable to create illust: %s" % (source.ILLUST_SHORTLINK % site_illust_id), upload)
            return
    elif CheckRequery(illust):
        UpdateIllustFromSource(illust, source)
    # The artist will have already been created in the create illust step if it didn't exist
    if CheckRequery(illust.artist):
        UpdateArtistFromSource(illust.artist, source)
    if ConvertNetworkUpload(illust, upload, source):
        SetUploadStatus(upload, 'complete')
    elif IsDuplicate(upload):
        SetUploadStatus(upload, 'duplicate')
    else:
        SetUploadStatus(upload, 'error')


def ProcessFileUpload(upload):
    illust = upload.illust_url.illust
    source = GetSourceById(illust.site_id)
    if CheckRequery(illust):
        UpdateIllustFromSource(illust, source)
    if CheckRequery(illust.artist):
        UpdateArtistFromSource(illust.artist, source)
    if ConvertFileUpload(upload, source):
        SetUploadStatus(upload, 'complete')
    else:
        SetUploadStatus(upload, 'error')


# #### Booru functions

def AddDanbooruArtists(url, danbooru_artists, db_boorus, db_artists):
    artist = next(filter(lambda x: x.booru_search_url == url, db_artists))
    for danbooru_artist in danbooru_artists:
        booru = next(filter(lambda x: x.danbooru_id == danbooru_artist['id'], db_boorus), None)
        if booru is None:
            booru = CreateBooruFromParameters(
                {'danbooru_id': danbooru_artist['id'], 'current_name': danbooru_artist['name']})
        BooruAppendArtist(booru, artist)


# #### Scheduled functions

def CheckPendingUploads():
    # UPLOAD_SEM.acquire()
    print("\n<upload semaphore acquire>\n")
    posts = []
    try:
        while True:
            print("Current upload count:", SESSION.query(Upload).count())
            upload_ids = GetPendingUploadIDs()
            for upload_id in upload_ids:
                # Must retrieve the upload with Flask session object for updating/appending to work
                upload = GetUploadWait(upload_id)
                if upload is None:
                    raise Exception("\aUnable to find upload with upload id: %d" % upload_id)
                if not ProcessUploadWrap(upload):
                    return
                posts.extend(upload.posts)
            else:
                print("No pending uploads.")
                break
            time.sleep(5)
    finally:
        if len(posts) > 0:
            scheduler.add_job(ProcessSimilarity)
            scheduler.add_job(CheckForNewArtistBoorus)
            # SCHED.add_job(CheckPostsForDanbooruID, args=(posts,))
            pass
        #  UPLOAD_SEM.release()
        print("\n<upload semaphore release>\n")


def CheckForNewArtistBoorus():
    LoadBooruArtistData()
    page = Artist.query.filter(Artist.id > BOORU_ARTISTS_DATA['last_checked_artist_id'],
                               not_(Artist.boorus.any())).paginate(per_page=100)
    max_artist_id = 0
    while True:
        if len(page.items) == 0:
            break
        query_urls = [artist.booru_search_url for artist in page.items]
        results = GetArtistsByMultipleUrls(query_urls)
        if results['error']:
            print("Danbooru error:", results)
            break
        booru_artist_ids = set(
            artist['id'] for artist in itertools.chain(*[results['data'][url] for url in results['data']]))
        boorus = Booru.query.filter(Booru.danbooru_id.in_(booru_artist_ids)).all()
        for url in results['data']:
            AddDanbooruArtists(url, results['data'][url], boorus, page.items)
        max_artist_id = max(max_artist_id, *[artist.id for artist in page.items])
        SaveLastCheckArtistId(max_artist_id)
        if not page.has_next:
            break
        page = page.next()


def ExpireUploads():
    expired_uploads = Upload.query.filter(Upload.created < MinutesAgo(5)).filter_by(status="processing").all()
    print("Uploads to expire:", len(expired_uploads))
    for upload in expired_uploads:
        SetUploadStatus(upload, 'complete')
        database.local.CreateAndAppendError('worker.ExpireUploads', "Upload has expired.", upload)


def ExpungeCacheRecords():
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
