# WORKER.PY

# ## PYTHON IMPORTS
import os
import time
from flask import request, abort, render_template
import atexit
import random
import threading
from PIL import Image
import imagehash
import distance
import requests
from io import BytesIO
from sqlalchemy import func
from sqlalchemy.orm import selectinload
import threading
from argparse import ArgumentParser
from apscheduler.schedulers.background import BackgroundScheduler

# ## LOCAL IMPORTS
from app import PREBOORU_APP, SESSION
import app.models
from app.models import Post
from app.cache import MediaFile
from app.similarity.similarity_result import SimilarityResult, HASH_SIZE
from app.similarity.similarity_result3 import SimilarityResult3
from app.similarity.similarity_pool import SimilarityPool
from app.similarity.similarity_pool_element import SimilarityPoolElement
from app.logical.file import PutGetRaw, CreateDirectory
from app.logical.utility import GetCurrentTime, GetBufferChecksum, DaysFromNow, GetFileExtension, GetHTTPFilename, AddDictEntry
from app.logical.network import GetHTTPFile
from app.storage import CACHE_DATA_DIRECTORY, CACHE_NETWORK_URLPATH
import app.sources.twitter
from app.sources import base as BASE_SOURCE
from app.logical.file import LoadDefault, PutGetJSON
from app.config import workingdirectory, datafilepath

#### GLOBAL VARIABLES

SERVER_PID_FILE = workingdirectory + datafilepath + 'similarity-server-pid.json'
SERVER_PID = next(iter(LoadDefault(SERVER_PID_FILE, [])), None)

SCHED = None
SEM = threading.Semaphore()

class NoSource():
    @staticmethod
    def SmallImageUrl(url):
        return url
    @staticmethod
    def NormalizedImageUrl(url):
        return url
    @staticmethod
    def GetMediaExtension(url):
        return GetFileExtension(GetHTTPFilename(url))
    IMAGE_HEADERS = {}

#### FUNCTIONS

@atexit.register
def Cleanup():
    if SERVER_PID is not None:
        PutGetJSON(SERVER_PID_FILE, 'w', [])
    if SCHED is not None and SCHED.running:
        SCHED.shutdown()

@PREBOORU_APP.route('/check_similarity.json', methods=['GET'])
def check_similarity():
    request_urls = request.args.getlist('urls[]')
    include_posts = request.args.get('include_posts', type=bool, default=False)
    print("check_similarity", request_urls, include_posts)
    if request_urls is None:
        return {'error': True, 'message': "Must include url."}
    similar_results = []
    for image_url in request_urls:
        source = BASE_SOURCE.GetImageSource(image_url) or NoSource()
        download_url = source.SmallImageUrl(image_url) if source is not None else image_url
        media = MediaFile.query.filter_by(media_url=download_url).first()
        if media is None:
            print("Download url:", download_url)
            starttime = time.time()
            print(image_url, download_url, source.IMAGE_HEADERS)
            buffer = GetHTTPFile(download_url, headers=source.IMAGE_HEADERS)
            print("Network time:", time.time() - starttime)
            if isinstance(buffer, Exception):
                return {'error': True, 'message': "Exception processing download: %s" % repr(buffer)}
            if isinstance(buffer, requests.Response):
                return {'error': True, 'message': "HTTP %d - %s" % (buffer.status_code, buffer.reason)}
            try:
                file_imgdata = BytesIO(buffer)
                image = Image.open(file_imgdata)
            except Exception as e:
                return {'error': True, 'message': "Error processing image data: %s" % repr(e)}
            md5 = GetBufferChecksum(buffer)
            extension = source.GetMediaExtension(download_url)
            media = MediaFile(md5=md5, file_ext=extension, media_url=download_url, expires=DaysFromNow(1))
            CreateDirectory(CACHE_DATA_DIRECTORY)
            PutGetRaw(media.file_path, 'wb', buffer)
            SESSION.add(media)
            SESSION.commit()
        else:
            print("Cache Hit:", media)
            image = Image.open(media.file_path)
        image = image.copy().convert("RGB")
        image_hash = str(imagehash.whash(image, hash_size=HASH_SIZE))
        print("Image hash:", image_hash)
        #smatches = SimilarityResult.query.filter(SimilarityResult.cross_similarity_clause2(image_hash)).all()
        ratio = round(image.width / image.height, 4)
        smatches = GetSimilarMatches(image_hash, ratio)
        print("Similar matches:", len(smatches))
        start_time = time.time()
        score_results = CheckSimilarMatchScores(smatches, image_hash, 90.0)
        end_time = time.time()
        if include_posts:
            post_ids = [result['post_id'] for result in score_results]
            posts = app.models.Post.query.filter(app.models.Post.id.in_(post_ids)).all()
            for result in score_results:
                post = next(filter(lambda x: x.id == result['post_id'], posts), None)
                result['post'] = post.to_json() if post is not None else post
        normalized_url = source.NormalizedImageUrl(image_url)
        print("url:", normalized_url, "hash:", image_hash, "numfound:", len(smatches), "time:", end_time - start_time)
        similar_results.append({'image_url': normalized_url, 'post_results': score_results, 'cache': media.file_url})
    return {'error': False, 'similar_results': similar_results}

@PREBOORU_APP.route('/check_posts', methods=['GET'])
def check_posts():
    if SEM._value > 0:
        SCHED.add_job(ProcessSimilarity)
        return "Begin processing similarity..."
    return "Similarity already processing!"

@PREBOORU_APP.route('/generate_similarity.json', methods=['POST'])
def generate_similarity():
    post_ids = request.args.getlist('post_ids[]', type=int)
    if post_ids is None:
        return {'error': True, 'message': "Must include post_ids."}
    SEM.acquire()
    print("<semaphore acquire>")
    posts = Post.query.filter(Post.id.in_(post_ids)).all()
    results = SimilarityResult.query.filter(SimilarityResult.post_id.in_(post_ids)).all()
    for post in posts:
        result = next(filter(lambda x: x.post_id == post.id, results), None)
        if result is None:
            GeneratePostSimilarity(post)
        else:
            RegeneratePostSimilarity(result, post)
    SESSION.commit()
    return {'error': False}

# ## GLOBAL VARIABLES

TOTAL_BITS = HASH_SIZE * HASH_SIZE

# ### FUNCTIONS

def GetSimilarMatches(image_hash, ratio):
    # %1 swing in ratio
    ratio_low = round(ratio * 99, 4) / 100
    ratio_high = round(ratio * 101, 4) / 100
    q = SimilarityResult.query
    q = q.filter(SimilarityResult.ratio.between(ratio_low, ratio_high))
    q = q.filter(SimilarityResult.cross_similarity_clause2(image_hash))
    return q.all()

def GeneratePostSimilarity(post):
    image = Image.open(post.preview_path)
    image_hash = imagehash.whash(image, hash_size=HASH_SIZE)
    ratio = round(post.width / post.height, 4)
    simresult = SimilarityResult(post_id=post.id, image_hash=str(image_hash), ratio=ratio)
    SESSION.add(simresult)
    #PopulateSimilarityPools(simresult)

def PopulateSimilarityPools(sdata):
    current_time = GetCurrentTime()
    smatches = SimilarityResult.query.filter(SimilarityResult.cross_similarity_clause1(sdata.image_hash), SimilarityResult.post_id != sdata.post_id).all()
    start_time = time.time()
    score_results = CheckSimilarMatchScores(smatches, sdata.image_hash, 90.0)
    print("Score results:", score_results)
    end_time = time.time()
    pool = SimilarityPool.query.filter_by(post_id=sdata.post_id).first()
    if pool is None:
        pool = SimilarityPool(post_id=sdata.post_id, created=current_time)
        SESSION.add(pool)
    pool.total_results = len(smatches)
    pool.calculation_time = round(end_time - start_time, 2)
    pool.updated=current_time
    SESSION.commit()
    if len(score_results) == 0:
        print("No matching results found.")
        return
    pool.update(score_results)
    result_post_ids = [result['post_id'] for result in score_results]
    result_pools = SimilarityPool.query.filter(SimilarityPool.post_id.in_(result_post_ids)).all()
    for result in score_results:
        inverse_result = {'post_id': sdata.post_id, 'score': result['score']}
        print("Adding inverse result:", inverse_result)
        pool = next(filter(lambda x: x.post_id == result['post_id'], result_pools), None)
        if pool is None:
            pool = SimilarityPool(post_id=sdata.post_id, updated=current_time, created=current_time, total_results=0, calculation_time=0.0)
            SESSION.add(pool)
            SESSION.commit()
        pool.append(inverse_result)


def RegeneratePostSimilarity(result,post):
    image = Image.open(post.preview_path)
    image_hash = imagehash.whash(image, hash_size=HASH_SIZE)
    result.image_hash = str(image_hash)

def HexToBinary(inhex):
    return bin(int(inhex, 16))[2:].zfill(len(inhex*4))

def CheckSimilarMatchScores(similarity_results, image_hash, min_score):
    found_results = []
    image_binary_string = HexToBinary(image_hash)
    hamming_time = 0
    for sresult in similarity_results:
        sresult_binary_string = HexToBinary(sresult.image_hash)
        starttime = time.time()
        mismatching_bits = distance.hamming(image_binary_string, sresult_binary_string)
        endtime = time.time()
        hamming_time += (endtime - starttime)
        miss_ratio = mismatching_bits / TOTAL_BITS
        score = round((1 - miss_ratio) * 100, 2)
        if score >= min_score:
            data = {
                'post_id': sresult.post_id,
                'score': score,
            }
            found_results.append(data)
    print("Hamming time:", hamming_time)
    return found_results


def GenerateSimilarityResults(args):
    if args.expunge:
        SimilarityResult.query.delete()
        SESSION.commit()
    max_post_id = SESSION.query(func.max(SimilarityResult.post_id)).scalar()
    page = Post.query.filter(Post.id > max_post_id).paginate(per_page=100)
    print("Generate similarity results:")
    while True:
        print("\n%d/%d" % (page.page, page.pages))
        for post in page.items:
            
            GeneratePostSimilarity(post)
            print('.', end="", flush=True)
        SESSION.commit()
        if not page.has_next:
            break
        page = Post.query.filter(Post.id > max_post_id).paginate(page=page.next_num, per_page=100)
    print("Done!")

def GenerateSimilarityPools(args):
    query = SimilarityResult.query
    if args.lastid is not None:
        query = query.filter(SimilarityResult.post_id >= args.lastid)
    page = query.paginate(per_page=100)
    print("Generate similarity results:")
    while True:
        print("\n%d/%d" % (page.page, page.pages))
        for sdata in page.items:
            current_time = GetCurrentTime()
            start_time = time.time()
            smatches = SimilarityResult.query.filter(SimilarityResult.cross_similarity_clause1(sdata.image_hash), SimilarityResult.post_id != sdata.post_id).all()
            score_results = CheckSimilarMatchScores(smatches, sdata.image_hash, 90.0)
            end_time = time.time()
            main_pool = SimilarityPool.query.filter_by(post_id=sdata.post_id).first()
            if main_pool is None:
                main_pool = SimilarityPool(post_id=sdata.post_id, created=current_time)
                SESSION.add(main_pool)
            main_pool.total_results = len(smatches)
            main_pool.calculation_time = round(end_time - start_time, 2)
            main_pool.updated = current_time
            SESSION.commit()
            sibling_post_ids = [result['post_id'] for result in score_results]
            sibling_pools = SimilarityPool.query.options(selectinload(SimilarityPool.elements)).filter(SimilarityPool.post_id.in_(sibling_post_ids)).all()
            INDEX_POOL_BY_POST_ID = {pool.post_id: pool for pool in sibling_pools}
            add_pools = []
            for post_id in sibling_post_ids:
                if post_id not in INDEX_POOL_BY_POST_ID:
                    pool = SimilarityPool(post_id=post_id, created=current_time, updated=current_time, calculation_time=0.0, total_results=0)
                    add_pools.append(pool)
                    INDEX_POOL_BY_POST_ID[post_id] = pool
            if len(add_pools) > 0:
                SESSION.add_all(add_pools)
                SESSION.commit()
            # Need to check for existing score results
            main_post_ids = [element.post_id for element in main_pool.elements]
            INDEX_POST_IDS_BY_POST_ID = {pool.post_id: [element.post_id for element in pool.elements] for pool in sibling_pools}
            for result in score_results:
                if result['post_id'] in main_post_ids:
                    spe1 = next(filter(lambda x: x.post_id == result['post_id'], main_pool.elements))
                else:
                    spe1 = SimilarityPoolElement(pool_id=main_pool.id, **result)
                    SESSION.add(spe1)
                    SESSION.commit()
                sibling_pool_post_ids = INDEX_POST_IDS_BY_POST_ID[result['post_id']] if result['post_id'] in INDEX_POST_IDS_BY_POST_ID else []
                if sdata.post_id in sibling_pool_post_ids:
                    sibling_pool = INDEX_POOL_BY_POST_ID[result['post_id']]
                    spe2 = next(filter(lambda x: x.post_id == sdata.post_id, sibling_pool.elements))
                else:
                    sibling_pool_id = INDEX_POOL_BY_POST_ID[result['post_id']].id
                    spe2 = SimilarityPoolElement(pool_id=sibling_pool_id, post_id=sdata.post_id, score=result['score'])
                    SESSION.add(spe2)
                    SESSION.commit()
                spe1.sibling_id = spe2.id
                spe2.sibling_id = spe1.id
                SESSION.commit()
            print('.', end="", flush=True)
        if not page.has_next:
            break
        page = page.next()
    print("Done!")


def FixupSimilarityPools(args):
    print("Getting all similarity pools.")
    all_similarity_pools = SimilarityPool.query.all()
    print("Getting all pools elements.")
    all_pool_elements = SimilarityPoolElement.query.all()
    POOL_MAP = {pool.id: pool.post_id for pool in all_similarity_pools}
    ELEMENT_POST_MAP = {pool.post_id: [] for pool in all_similarity_pools}
    ELEMENT_INDEX_BY_POOL_POST_ID = {}
    for element in all_pool_elements:
        post_id = POOL_MAP[element.pool_id]
        AddDictEntry(ELEMENT_POST_MAP, post_id, element.post_id)
        indexkey = str(element.pool_id) + '-' + str(element.post_id)
        ELEMENT_INDEX_BY_POOL_POST_ID[indexkey] = element
    POOL_INDEX_BY_POST_ID = {}
    for pool in all_similarity_pools:
        POOL_INDEX_BY_POST_ID[pool.post_id] = pool
    for post_id_1 in ELEMENT_POST_MAP:
        post_ids_1 = ELEMENT_POST_MAP[post_id_1]
        for post_id_2 in post_ids_1:
            post_ids_2 = ELEMENT_POST_MAP[post_id_2]
            if post_id_1 not in post_ids_2:
                print(post_id_1, post_id_2, post_ids_1, post_ids_2)
                pool_id_1 = POOL_MAP[post_id_1]
                pool_id_2 = POOL_MAP[post_id_2]
                print("Finding element.")
                #element_2 = next(filter(lambda x: x.pool_id == pool_id_1 and x.post_id == post_id_2, all_pool_elements))
                indexkey = str(pool_id_1) + '-' + str(post_id_2)
                element_2 = ELEMENT_INDEX_BY_POOL_POST_ID[indexkey]
                print("Finding pool.")
                #pool_2 = next(filter(lambda x: x.post_id == post_id_2, all_similarity_pools))
                pool_2 = POOL_INDEX_BY_POST_ID[post_id_2]
                print(element_2, pool_2)
                score_result = {'post_id': post_id_1, 'score': element_2.score}
                print(score_result)
                #input("####CHECK####")
                pool_2.append(**score_result)
                #input("####BREAK####")

def CompareSimilarityResults(args):
    page = SimilarityResult.query.paginate(per_page=100)
    print("Generate similarity results:")
    while True:
        print("\n%d/%d" % (page.page, page.pages))
        for sdata in page.items:
            if sdata.post_id < 15055:
                continue
            pool = SimilarityPool.query.filter_by(post_id=sdata.post_id).first()
            if pool is None:
                print("Did not find pool for post #", sdata.post_id)
                continue
            smatches = SimilarityResult.query.filter(SimilarityResult.cross_similarity_clause2(sdata.image_hash)).all()
            start_time = time.time()
            score_results = CheckSimilarMatchScores(smatches, sdata.image_hash, 80.0)
            end_time = time.time()
            score_results = sorted(score_results, key=lambda x: x['score'], reverse=True)
            print("post #", sdata.post_id, "numfound:", len(smatches), "time:", end_time - start_time)
            pool_elements = sorted(pool.elements, key=lambda x: x.score, reverse=True)
            comp1_post_ids = [element.post_id for element in pool_elements if element.score > 90.0]
            comp2_post_ids = [result['post_id'] for result in score_results if result['score'] > 90.0]
            unique1_post_ids = [post_id for post_id in comp1_post_ids if post_id not in comp2_post_ids]
            unique2_post_ids = [post_id for post_id in comp1_post_ids if post_id not in comp1_post_ids]
            #unique1_post_ids = list(set(comp1_post_ids).difference(comp2_post_ids))
            #unique2_post_ids = list(set(comp2_post_ids).difference(comp1_post_ids))
            if len(unique1_post_ids) > 0:
                print("Method 1 unique results")
                for post_id in unique1_post_ids:
                    element = next(filter(lambda x: x.post_id == post_id, pool.elements))
                    print("post #", element.post_id, "score:", element.score)
                check_url = "http://127.0.0.1:5000/posts?search[order]=custom&search[id]=%d,%s" % (sdata.post_id, ','.join(map(str,unique1_post_ids)))
                print(check_url)
                os.startfile(check_url)
            if len(unique2_post_ids) > 0:
                print("Method 2 unique results")
                for post_id in unique2_post_ids:
                    result = next(filter(lambda x: x['post_id'] == post_id, score_results))
                    print("post #", result['post_id'], "score:", result['score'])
            if len(unique1_post_ids) == 0 and len(unique2_post_ids) == 0:
                print("No differences found!")
                continue
            input("####")
        if not page.has_next:
            break
        page = SimilarityResult.query.paginate(page=page.next_num, per_page=100)
    print("Done!")

def TransferSimilarityResults(args):
    page = SimilarityResult.query.paginate(per_page=1000)
    print("Transferring similarity results:")
    while True:
        print("\n%d/%d" % (page.page, page.pages))
        for result in page.items:
            result3 = SimilarityResult3(post_id=result.post_id, image_hash=result.image_hash)
            SESSION.add(result3)
        SESSION.commit()
        if not page.has_next:
            break
        page = SimilarityResult.query.paginate(page=page.next_num, per_page=100)
    print("Done!")

def ProcessSimilarity():
    print("{ProcessSimilarity}")
    SEM.acquire()
    print("<semaphore acquire>")
    try:
        while True:
            if not ProcessSimilaritySet():
                break
    finally:
        SEM.release()
        print("\n<semaphore release>")

def ProcessSimilaritySet():
    max_post_id = SESSION.query(func.max(SimilarityResult.post_id)).scalar()
    page = Post.query.filter(Post.id > max_post_id).paginate(per_page=100)
    if len(page.items) == 0:
        return False
    print("Process similarity results:", max_post_id)
    while True:
        print("\n%d/%d" % (page.page, page.pages))
        for post in page.items:
            GeneratePostSimilarity(post)
            print('.', end="", flush=True)
        SESSION.commit()
        if not page.has_next:
            return True
        page = page.next()

def ChooseSimilarityResult():
    while True:
        keyinput = input("Post ID: ")
        if not keyinput:
            return
        if not keyinput.isdigit():
            print("Must enter a valid ID number.")
            continue
        post_id = int(keyinput)
        sresult = SimilarityResult.query.filter_by(post_id=post_id).first()
        if sresult is None:
            print("Post not found:", post_id)
            continue
        return sresult

def GetHTTPImage(url):
    print("Downloading:", url)
    for i in range(3):
        try:
            resp = requests.get(url, timeout=10)
        except (requests.exceptions.ReadTimeout,requests.exceptions.ConnectionError) as e:
            print("Server exception:", e)
            return -2
        if resp.status_code != 200:
            print("HTTP Error:", comic_id, resp.status_code, resp.reason)
            time.sleep(30)
            continue
        break
    else:
        print("Unable to download:", url)
        return -1
    return resp.content

def ComparePostSimilarity(args):
    sresult = ChooseSimilarityResult()
    if sresult is None:
        return
    print("Result hash:", sresult.image_hash)
    sresult_binary_string = HexToBinary(sresult.image_hash)
    while True:
        keyinput = input("Image URL: ")
        if not keyinput:
            break
        buffer = GetHTTPImage(keyinput)
        if type(buffer) is int:
            continue
        try:
            file_imgdata = BytesIO(buffer)
            image = Image.open(file_imgdata)
        except Exception as e:
            print("Unable to open image:", e)
            continue
        image.copy().convert("RGB")
        image_hash = str(imagehash.whash(image, hash_size=HASH_SIZE))
        print("Image hash:", image_hash)
        image_binary_string = HexToBinary(image_hash)
        mismatching_bits = distance.hamming(image_binary_string, sresult_binary_string)
        miss_ratio = mismatching_bits / TOTAL_BITS
        score = round((1 - miss_ratio) * 100, 2)
        print("Mismatching:", mismatching_bits, "Ratio:", miss_ratio, "Score:", score)

def StartServer(args):
    if args.title:
        os.system('title Similarity Server')
    global SCHED, SERVER_PID
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        SERVER_PID = os.getpid()
        PutGetJSON(SERVER_PID_FILE, 'w', [SERVER_PID])
        SCHED = BackgroundScheduler(daemon=True)
        #SCHED.add_job(CheckMissingSimilarity, 'interval', minutes=5)
        SCHED.add_job(ProcessSimilarity)
        SCHED.start()
    PREBOORU_APP.run(threaded=True, port=3000)

# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Worker to process uploads.")
    parser.add_argument('type', choices=['generate', 'pools', 'compare', 'comparepost', 'transfer', 'server', 'fixup'])
    parser.add_argument('--logging', required=False, default=False, action="store_true", help="Display the SQL commands.")
    parser.add_argument('--expunge', required=False, default=False, action="store_true", help="Expunge all similarity records.")
    parser.add_argument('--title', required=False, default=False, action="store_true", help="Adds server title to console window.")
    parser.add_argument('--lastid', required=False, type=int, help="Sets the last post ID to use.")
    args = parser.parse_args()
    if args.logging:
        import logging
        logging.basicConfig()
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    if args.type == 'generate':
        GenerateSimilarityResults(args)
    elif args.type == 'pools':
        GenerateSimilarityPools(args)
    elif args.type == 'compare':
        CompareSimilarityResults(args)
    elif args.type == 'comparepost':
        ComparePostSimilarity(args)
    elif args.type == 'transfer':
        TransferSimilarityResults(args)
    elif args.type == 'fixup':
        FixupSimilarityPools(args)
    elif args.type == 'server':
        StartServer(args)
