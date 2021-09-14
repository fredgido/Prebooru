# APP/STORAGE.PY

# ## LOCAL IMPORTS
import os

from . import SERVER_INFO
from .config import WORKING_DIRECTORY, IMAGE_FILEPATH

# ### GLOBAL VARIABLES

IMAGE_DIRECTORY = os.path.join(WORKING_DIRECTORY, IMAGE_FILEPATH, 'prebooru')

PREVIEW_DIMENSIONS = (300, 300)
SAMPLE_DIMENSIONS = (1280, 1920)

CACHE_DATA_DIRECTORY = os.path.join(IMAGE_DIRECTORY, 'cache') + os.path.sep


# ## FUNCTIONS

def DataDirectory(type, md5):
    return os.path.join(IMAGE_DIRECTORY, type, md5[0:2], md5[2:4]) + os.path.sep


def HasSample(width, height):
    return width > SAMPLE_DIMENSIONS[0] or height > SAMPLE_DIMENSIONS[1]


def HasPreview(width, height):
    return width > PREVIEW_DIMENSIONS[0] or height > PREVIEW_DIMENSIONS[1]

