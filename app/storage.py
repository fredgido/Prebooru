# APP/STORAGE.PY

# ##LOCAL IMPORTS
from .config import WORKING_DIRECTORY, IMAGE_FILEPATH, IMAGE_SERVER

# ###GLOBAL VARIABLES

IMAGE_DIRECTORY = WORKING_DIRECTORY + IMAGE_FILEPATH + 'prebooru\\'

PREVIEW_DIMENSIONS = (300, 300)
SAMPLE_DIMENSIONS = (1280, 1920)

CACHE_DATA_DIRECTORY = IMAGE_DIRECTORY + 'cache\\'
CACHE_NETWORK_URLPATH = IMAGE_SERVER + 'cache/'


# ##FUNCTIONS


def DataDirectory(type, md5):
    return IMAGE_DIRECTORY + '%s\\%s\\%s\\' % (type, md5[0:2], md5[2:4])


def NetworkDirectory(type, md5):
    return IMAGE_SERVER + '%s/%s/%s/' % (type, md5[0:2], md5[2:4])


def HasSample(width, height):
    return width > SAMPLE_DIMENSIONS[0] or height > SAMPLE_DIMENSIONS[1]


def HasPreview(width, height):
    return width > PREVIEW_DIMENSIONS[0] or height > PREVIEW_DIMENSIONS[1]
