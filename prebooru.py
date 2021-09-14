# PREBOORU.PY

# ## PYTHON IMPORTS
import os
import atexit
import time
from io import BytesIO

from sqlalchemy import func
from flask_apscheduler import APScheduler
import distance
import imagehash
from PIL import Image
import colorama
from flask_migrate import Migrate
from argparse import ArgumentParser

# ## LOCAL IMPORTS

from app import PREBOORU_APP, DB, SESSION
from app import controllers
from app import helpers
from app.logical.file import LoadDefault, PutGetJSON
from app.config import WORKING_DIRECTORY, DATA_FILEPATH, PREBOORU_PORT, DEBUG_MODE, VERSION, HAS_EXTERNAL_IMAGE_SERVER

# ## GLOBAL VARIABLES
from app.logical.network import GetHTTPFile
from app.logical.similarity import CheckSimilarMatchScores, ChooseSimilarityResult, PopulateSimilarityPools, \
    HexToBinary, GeneratePostSimilarity
from app.models import Post, SimilarityData, SimilarityPoolElement, SimilarityPool
from app.models.similarity_data import HASH_SIZE, TOTAL_BITS

SERVER_PID_FILE = WORKING_DIRECTORY + DATA_FILEPATH + 'prebooru-server-pid.json'
SERVER_PID = next(iter(LoadDefault(SERVER_PID_FILE, [])), None)

# Registering this with the Prebooru app so that DB commands can be executed with flask
# The environment variables need to be set for this to work, which can be done by executing
# the setup.bat script, then running "flask db" will show all of the available commands.
migrate = Migrate(PREBOORU_APP, DB, render_as_batch=True)  # noqa: F841


# ## FUNCTIONS

@atexit.register
def Cleanup():
    if SERVER_PID is not None:
        PutGetJSON(SERVER_PID_FILE, 'w', [])


def StartServer(args):
    global SERVER_PID
    if SERVER_PID is not None:
        print("Server process already running: %d" % SERVER_PID)
        input()
        exit(-1)
    if args.extension:
        try:
            from flask_flaskwork import Flaskwork
        except ImportError:
            print("Install flaskwork module: pip install flask-flaskwork --upgrade")
        else:
            Flaskwork(PREBOORU_APP)
    if args.title:
        os.system('title Prebooru Server')
    if not DEBUG_MODE or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        print("\n========== Starting server - Prebooru-%s ==========" % VERSION)
        SERVER_PID = os.getpid()
        PutGetJSON(SERVER_PID_FILE, 'w', [SERVER_PID])
    PREBOORU_APP.name = 'prebooru'
    if args.public:
        PREBOORU_APP.run(threaded=True, port=PREBOORU_PORT, host="0.0.0.0")
    else:
        PREBOORU_APP.run(threaded=True, port=PREBOORU_PORT)


def InitDB(args):
    check = input("This will destroy any existing information. Proceed (y/n)? ")
    if check.lower() != 'y':
        return
    from app.logical.file import CreateDirectory
    from app.config import DB_PATH, CACHE_PATH, SIMILARITY_PATH
    if args.new:
        if os.path.exists(DB_PATH):
            print("Deleting prebooru database!")
            os.remove(DB_PATH)
        if os.path.exists(CACHE_PATH):
            print("Deleting cache database!")
            os.remove(CACHE_PATH)
        if os.path.exists(SIMILARITY_PATH):
            print("Deleting similarity database!")
            os.remove(SIMILARITY_PATH)

    print("Creating tables")
    from app.models import NONCE  # noqa: F401, F811
    from app.cache import NONCE  # noqa: F401, F811
    from app.similarity import NONCE  # noqa: F401, F811
    CreateDirectory(DB_PATH)
    CreateDirectory(CACHE_PATH)
    CreateDirectory(SIMILARITY_PATH)
    DB.drop_all()
    DB.create_all()

    print("Setting current migration to HEAD")
    from flask_migrate import stamp
    migrate.init_app(PREBOORU_APP)
    with PREBOORU_APP.app_context():
        stamp()


def GenerateSimilarityResults(args):
    if args.expunge:
        SimilarityData.query.delete()
        SESSION.commit()
    max_post_id = SESSION.query(func.max(SimilarityData.post_id)).scalar() or 0
    page = Post.query.filter(Post.id > max_post_id).paginate(per_page=100)
    while True:
        print("\n%d/%d" % (page.page, page.pages))
        for post in page.items:
            GeneratePostSimilarity(post)
        if not page.has_next:
            break
        page = page.next()
    print("Done!")


def GenerateSimilarityPools(args):
    if args.expunge:
        SimilarityPoolElement.query.delete()  # This may not work due to the sibling relationship; may need to do a mass update first
        SESSION.commit()
        SimilarityPool.query.delete()
        SESSION.commit()
    max_post_id = SESSION.query(func.max(SimilarityPool.post_id)).scalar() or 0
    page = Post.query.filter(Post.id > max_post_id).with_entities(Post.id).paginate(per_page=100)
    while True:
        print("\n%d/%d" % (page.page, page.pages))
        all_post_ids = [x[0] for x in page.items]
        all_sdata_items = SimilarityData.query.filter(SimilarityData.post_id.in_(all_post_ids)).all()
        for post_id in all_post_ids:
            sdata_items = [sdata for sdata in all_sdata_items if sdata.post_id == post_id]
            PopulateSimilarityPools(sdata_items)
        if not page.has_next:
            break
        page = page.next()
    print("Done!")


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
        buffer = GetHTTPFile(keyinput)
        if type(buffer) is not bytes:
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


def ComparePosts(args):
    page = Post.query.order_by(Post.id.asc()).paginate(per_page=100)
    while True:
        print("\n%d/%d" % (page.page, page.pages))
        for post in page.items:
            print("Post #", post.id)
            starttime = time.time()
            ratio = round(post.width / post.height, 4)
            simresults = SimilarityData.query.filter_by(post_id=post.id).all()
            if post.file_ext != 'mp4':
                full_image = Image.open(post.file_path)
                full_image = full_image.convert("RGB")
                full_image_hash = str(imagehash.whash(full_image, hash_size=HASH_SIZE))
                print("Full convert time:", time.time() - starttime)
                score_results = CheckSimilarMatchScores(simresults, full_image_hash, 90.0)
                if len(score_results) == 0:
                    print("FULL SIZE ADD")
                    simresult = SimilarityData(post_id=post.id, image_hash=full_image_hash, ratio=ratio)
                    SESSION.add(simresult)
                    SESSION.commit()
                    simresults.append(simresult)
                if post.file_path == post.sample_path:
                    continue
            starttime = time.time()
            sample_image = Image.open(post.sample_path)
            sample_image = sample_image.convert("RGB")
            sample_image_hash = str(imagehash.whash(sample_image, hash_size=HASH_SIZE))
            print("Sample convert time:", time.time() - starttime)
            score_results = CheckSimilarMatchScores(simresults, sample_image_hash, 90.0)
            if len(score_results) == 0:
                print("SAMPLE SIZE ADD")
                simresult = SimilarityData(post_id=post.id, image_hash=sample_image_hash, ratio=ratio)
                SESSION.add(simresult)
                SESSION.commit()
        if not page.has_next:
            break
        page = page.next()
    print("Done!")



def Main(args):
    switcher = {
        'server': StartServer,
        'init': InitDB,
        'generate': GenerateSimilarityResults,
        'pools': GenerateSimilarityPools,
        'compare': ComparePostSimilarity,
        'compareposts': ComparePosts,
    }
    switcher[args.type](args)


# ### INITIALIZATION

os.environ['FLASK_ENV'] = 'development' if DEBUG_MODE else 'production'

colorama.init(autoreset=True)

PREBOORU_APP.register_blueprint(controllers.illust.bp)
PREBOORU_APP.register_blueprint(controllers.illust_url.bp)
PREBOORU_APP.register_blueprint(controllers.artist.bp)
PREBOORU_APP.register_blueprint(controllers.artist_url.bp)
PREBOORU_APP.register_blueprint(controllers.booru.bp)
PREBOORU_APP.register_blueprint(controllers.upload.bp)
PREBOORU_APP.register_blueprint(controllers.post.bp)
PREBOORU_APP.register_blueprint(controllers.pool.bp)
PREBOORU_APP.register_blueprint(controllers.pool_element.bp)
PREBOORU_APP.register_blueprint(controllers.tag.bp)
PREBOORU_APP.register_blueprint(controllers.notation.bp)
PREBOORU_APP.register_blueprint(controllers.error.bp)
PREBOORU_APP.register_blueprint(controllers.proxy.bp)
PREBOORU_APP.register_blueprint(controllers.static.bp)
PREBOORU_APP.register_blueprint(controllers.similarity.bp)
PREBOORU_APP.register_blueprint(controllers.similarity_pool.bp)
PREBOORU_APP.register_blueprint(controllers.similarity_pool_element.bp)
if not HAS_EXTERNAL_IMAGE_SERVER:
    PREBOORU_APP.register_blueprint(controllers.images.bp)

PREBOORU_APP.jinja_env.globals.update(helpers=helpers)
PREBOORU_APP.jinja_env.add_extension('jinja2.ext.do')
PREBOORU_APP.jinja_env.add_extension('jinja2.ext.loopcontrols')

# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Server to process network requests.")
    parser.add_argument('type', choices=['init', 'server'])
    parser.add_argument('--new', required=False, default=False, action="store_true", help="Start with a new database file.")
    parser.add_argument('--extension', required=False, default=False, action="store_true", help="Enable Chrome extension.")
    parser.add_argument('--title', required=False, default=False, action="store_true", help="Adds server title to console window.")
    parser.add_argument('--public', required=False, default=False, action="store_true", help="Makes the server visible to other computers.")
    args = parser.parse_args()
    Main(args)
