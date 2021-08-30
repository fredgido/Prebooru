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
        return {'error': True, 'message': "Unable to contact worker server: %s" % str(e)}
    return {'error': False}


def SimilarityCheckPosts():
    try:
        requests.get('http://127.0.0.1:%d/check_posts' % SIMILARITY_PORT, timeout=2)
    except Exception as e:
        return {'error': True, 'message': "Unable to contact similarity server: %s" % str(e)}
    return {'error': False}


def SimilarityRegeneratePost(post_id):
    try:
        data = requests.get('http://127.0.0.1:%d/post_ids[]=%d' % (SIMILARITY_PORT, post_id), timeout=2)
    except Exception as e:
        return {'error': True, 'message': "Unable to contact similarity server: %s" % str(e)}
    return data
