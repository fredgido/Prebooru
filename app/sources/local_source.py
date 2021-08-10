# APP/SOURCES/LOCAL_SOURCE.PY

# ## PYTHON IMPORTS
import requests

# ## LOCAL IMPORTS
from ..config import WORKER_PORT, SIMILARITY_PORT


# ## FUNCTIONS

def WorkerCheckUploads():
    try:
        requests.get('http://127.0.0.1:%d/check_uploads' % WORKER_PORT, timeout=2)
    except Exception as e:
        print("Unable to contact worker server:", e)


def SimilarityCheckPosts():
    try:
        requests.get('http://127.0.0.1:%d/check_posts' % SIMILARITY_PORT, timeout=2)
    except Exception as e:
        print("Unable to contact similarity server:", e)
