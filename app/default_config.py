# APP/DEFAULT_CONFIG.PY

# ##WINDOWS###
"""Filepaths need to end with a double backslash ('\\')"""
"""All backslashes ('\') in a filepath need to be double escaped ('\\')"""
workingdirectory = "C:\\Temp\\"
datafilepath = "data\\"
imagefilepath = "pictures\\"

# Relative path to the DB file
DB_PATH = r'db\prebooru.db'
CACHE_PATH = r'db\cache.db'
SIMILARITY_PATH = r'db\similarity.db'

# ##LINUX###
'''
"""Filepaths need to end with a forwardslash ('/')"""
workingdirectory = "/home/USERNAME/temp/"
datafilepath = "data/"
jsonfilepath = "json/"
imagefilepath = "pictures/"

# Relative path to the DB file
DB_PATH = 'db/prebooru.db'
'''

# ##GENERAL###

# The user ID of the system
SYSTEM_USER_ID = 2

# Log into Pixiv and get this value from the cookie PHPSESSID
PIXIV_PHPSESSID = None
