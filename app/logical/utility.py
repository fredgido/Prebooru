# APP/LOGICAL/UTILITY.PY

# ##PYTHON IMPORTS
import re
import json
import iso8601
import hashlib
import datetime


# ##FUNCTIONS


def ProcessTimestamp(timestring):
    """Get seconds from the Epoch for timestamps"""
    return round(iso8601.parse_date(timestring).timestamp())


def GetBufferChecksum(buffer):
    hasher = hashlib.md5()
    hasher.update(buffer)
    return hasher.hexdigest()


def GetHTTPFilename(webpath):
    start = webpath.rfind('/') + 1
    isextras = webpath.rfind('?')
    end = isextras if isextras > 0 else len(webpath) + 1
    return webpath[start:end]


def GetFileExtension(filepath):
    return filepath[filepath.rfind('.') + 1:]


def GetDirectory(filepath):
    return filepath[:filepath.rfind('\\') + 1]


def DecodeUnicode(byte_string):
    try:
        decoded_string = byte_string.decode('utf')
    except Exception:
        print("Unable to decode data!")
        return
    return decoded_string


def DecodeJSON(string):
    try:
        data = json.loads(string)
    except Exception:
        print("Invalid data!")
        return
    return data


def GetCurrentTime():
    t = datetime.datetime.utcnow()
    return t - datetime.timedelta(microseconds=t.microsecond)

def DaysAgo(days):
    return GetCurrentTime() - datetime.timedelta(days=days)

def DaysFromNow(days):
    return GetCurrentTime() + datetime.timedelta(days=days)

def MinutesAgo(minutes):
    return GetCurrentTime() - datetime.timedelta(minutes=minutes)

def SafeGet(input_dict, *keys):
    for key in keys:
        try:
            input_dict = input_dict[key]
        except (KeyError, TypeError):
            return None
    return input_dict


def IsTruthy(string):
    truth_match = re.match(r'^(?:t(?:rue)?|y(?:es)|1)$', string, re.IGNORECASE)
    return truth_match is not None


def IsFalsey(string):
    false_match = re.match(r'^(?:f(?:alse)?|n(?:o)|0)$', string, re.IGNORECASE)
    return false_match is not None


def EvalBoolString(string):
    if IsTruthy(string):
        return True
    if IsFalsey(string):
        return False


def StaticVars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate


def UniqueObjects(objs):
    seen = set()
    output = []
    for obj in objs:
        if obj.id not in seen:
            seen.add(obj.id)
            output.append(obj)
    return output

'''
DOESN'T WORK
def pmemoize(func):
    """Simple memoize for non-mutating property methods"""
    def memoized_func(*args,**kwargs):
        if memoized_func.cache is not None:
            return memoized_func.cache
        memoized_func.cache = func(*args,**kwargs)
        return memoized_func.cache
    setattr(memoized_func, 'cache', None)
    return memoized_func
'''
