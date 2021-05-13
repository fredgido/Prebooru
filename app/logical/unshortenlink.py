import re
import requests
from ..models import Description, ArtistUrl
from .. import session as SESSION

"""
http://u0u1.net/Y8lp
"""
SHORTURL_RG = re.compile(r'^http://\w{3,5}\.\w{2,4}/\w{3,6}$')
"""
http://urx.morimo.info/Y8lp?h=u0u1.net
"""
MORIMO_RG = re.compile('^http://urx\.morimo\.info/\w{3,6}\?h=\w{3,5}\.\w{2,4}$')

TCO_RG = re.compile(r'https?://t\.co/\w+')


def UnshortenAllLinks():
    UnshortenTcoLinks()

# General


def GetShortTransformations(text):
    shortlinks = SHORTURL_RG.findall(text)
    print("GetShortTransformations:", len(shortlinks))
    transforms = {}
    for link in shortlinks:
        redirect_link = GetShortRedirect(link)
        if redirect_link is not None:
            transforms[link] = redirect_link
    return transforms


def GetShortRedirect(link):
    try:
        resp = requests.get(link, allow_redirects=None, timeout=5)
    except:
        print("Error getting URL redirect:", link)
        return
    if resp.status_code == 301 and 'location' in resp.headers:
        redirect_link = resp.headers['location']
        if IsMorimoLink(redirect_link):
            redirect_link = GetShortRedirect(redirect_link)
        return redirect_link

# Morimo

def IsMorimoLink(link):
    return MORIMO_RG.match(link) is not None


# T.CO -- Twitter

def UnshortenTcoLinks():
    UnshortenTcoDescriptions()
    UnshortenTcoArtistUrls()


def UnshortenTcoArtistUrls():
    print("UnshortenTcoArtistUrls")
    tco_artist_urls = ArtistUrl.query.filter(ArtistUrl.url.like('https://t.co/%')).all()
    for artist_url in tco_artist_urls:
        artist_url.url = UnshortenTcoText(artist_url.url)
    if len(tco_artist_urls):
        SESSION.commit()


def UnshortenTcoDescriptions():
    print("UnshortenTcoDescriptions")
    tco_descriptions = Description.query.filter(Description.body.like('%https://t.co/%')).all()
    for descr in tco_descriptions:
        descr.body = UnshortenTcoText(descr.body)
    if len(tco_descriptions):
        SESSION.commit()


def UnshortenTcoText(text):
    transforms = GetTcoTransforms(text)
    for key in transforms:
        text = text.replace(key, transforms[key])
    return text


def GetTcoTransforms(text):
    tco_links = TCO_RG.findall(text)
    transforms = {}
    print("GetTcoTransforms:", len(tco_links))
    for link in tco_links:
        transforms[link] = None
        try:
            resp = requests.get(link, allow_redirects=None, timeout=5)
        except:
            print("Error getting URL redirect:", link)
            continue
        if resp.status_code == 301 and 'location' in resp.headers:
            transforms[link] = resp.headers['location']
    return transforms
