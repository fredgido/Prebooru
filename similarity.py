# WORKER.PY

# ## PYTHON IMPORTS
import os
import time
from flask import request
import atexit
import random
import threading
from PIL import Image
import imagehash
import distance

# ## LOCAL IMPORTS
from app import app as APP
from app import session as SESSION
from app.models import Post
from app.similarity.similarity_result import SimilarityResult, HASH_SIZE
from app.similarity.similarity_result3 import SimilarityResult3
from app.similarity.similarity_pool import SimilarityPool
from app.logical.utility import GetCurrentTime
from argparse import ArgumentParser


# ## GLOBAL VARIABLES

TOTAL_BITS = HASH_SIZE * HASH_SIZE

# ### FUNCTIONS

def GeneratePostSimilarity(post):
    image = Image.open(post.preview_path)
    hash = imagehash.whash(image, hash_size=HASH_SIZE)
    simresult = SimilarityResult(post_id=post.id, image_hash=str(hash))
    SESSION.add(simresult)

def CheckSimilarMatchScores(similarity_results, image_hash, min_score):
    found_results = []
    image_hashlist = imagehash.hex_to_flathash(image_hash, HASH_SIZE).hash[0]
    for sresult in similarity_results:
        sresult_hashlist = imagehash.hex_to_flathash(sresult.image_hash, HASH_SIZE).hash[0]
        mismatching_bits = distance.hamming(image_hashlist, sresult_hashlist)
        miss_ratio = mismatching_bits / TOTAL_BITS
        score = round((1 - miss_ratio) * 100, 2)
        if score >= min_score:
            data = {
                'post_id': sresult.post_id,
                'score': score,
            }
            found_results.append(data)
    return found_results


def GenerateSimilarityResults(args):
    if args.expunge:
        SimilarityResult.query.delete()
        SESSION.commit()
    page = Post.query.paginate(per_page=100)
    print("Generate similarity results:")
    while True:
        print("\n%d/%d" % (page.page, page.pages))
        for post in page.items:
            GeneratePostSimilarity(post)
            print('.', end="", flush=True)
        SESSION.commit()
        if not page.has_next:
            break
        page = Post.query.paginate(page=page.next_num, per_page=100)
    print("Done!")

def GenerateSimilarityPools(args):
    page = SimilarityResult.query.paginate(per_page=100)
    print("Generate similarity results:")
    while True:
        print("\n%d/%d" % (page.page, page.pages))
        for sdata in page.items:
            smatches = SimilarityResult.query.filter(SimilarityResult.cross_similarity_clause1(sdata.image_hash)).all()
            start_time = time.time()
            score_results = CheckSimilarMatchScores(smatches, sdata.image_hash, 80.0)
            end_time = time.time()
            pool = SimilarityPool.query.filter_by(post_id=sdata.post_id).first()
            if pool is not None:
                if len(pool.elements) > 0:
                    print('S', end="", flush=True)
                    continue
            else:
                pool = SimilarityPool(post_id=sdata.post_id, created=GetCurrentTime())
                SESSION.add(pool)
            pool.total_results = len(smatches)
            pool.calculation_time = round(end_time - start_time, 2)
            pool.updated=GetCurrentTime()
            SESSION.commit()
            pool.update(score_results)
            print('.', end="", flush=True)
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

# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Worker to process uploads.")
    parser.add_argument('type', choices=['generate', 'pools', 'transfer', 'server'])
    parser.add_argument('--logging', required=False, default=False, action="store_true", help="Display the SQL commands.")
    parser.add_argument('--expunge', required=False, default=False, action="store_true", help="Expunge all similarity records.")
    args = parser.parse_args()
    if args.logging:
        import logging
        logging.basicConfig()
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    if args.type == 'generate':
        GenerateSimilarityResults(args)
    elif args.type == 'pools':
        GenerateSimilarityPools(args)
    elif args.type == 'transfer':
        TransferSimilarityResults(args)
    elif args.type == 'server':
        APP.run(threaded=True, port=3000)
