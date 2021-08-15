# APP/HELPERS/NOTATIONS_HELPERS.PY

# ##PYTHON IMPORTS
import re
import html
from flask import Markup, url_for

# ##LOCAL IMPORTS
from .base_helper import ConvertStrToHTML, GeneralLink
from . import artists_helper as ARTIST
from . import illusts_helper as ILLUST


# ##GLOBAL VARIABLES

HTTP_RG = re.compile(r'(\b(?:http|https)(?::\/{2}[\w]+)(?:[\/|\.]?)(?:[^\s<>\uff08\uff09\u3011\u3000"\[\]]*))', re.ASCII)

APPEND_ATTRS = ['_pool', 'artist', 'illust', 'post']
APPEND_KEY_DICT = {
    '_pool': 'pool',
    'artist': 'artist',
    'illust': 'illust',
    'post': 'post',
}


# ## FUNCTIONS

# #### Helper functions

def IsGeneralForm(form):
    return (form.pool_id.data is None) and (form.artist_id.data is None) and (form.illust_id.data is None) and (form.post_id.data is None)


# #### General functions

def ConvertToHTML(notation):
    links = HTTP_RG.findall(notation.body)
    output_html = html.escape(notation.body)
    for link in links:
        escaped_link = re.escape(html.escape(link))
        link_match = re.search(escaped_link, output_html)
        if link_match is None:
            continue
        html_link = '<a href="%s">%s</a>' % (link, link)
        output_html = output_html[:link_match.start()] + html_link + output_html[link_match.end():]
    output_html = re.sub(r'\r?\n', '<br>', output_html)
    return Markup(output_html)


# #### Route functions

# ###### INDEX

def Excerpt(notation):
    lines = re.split(r'\r?\n', notation.body)
    return ConvertStrToHTML(lines[0][:50] + ('...' if len(lines[0]) > 50 else ''))


# ###### SHOW

def ItemLink(item):
    return GeneralLink(ItemLinkTitle(item), item.show_url)


def ItemLinkTitle(item):
    if item.__table__.name == 'pool':
        return item.name
    if item.__table__.name == 'artist':
        return ARTIST.ShortLink(item)
    if item.__table__.name == 'illust':
        return ILLUST.ShortLink(item)
    return item.header


def HasAppendItem(notation):
    return any((getattr(notation, attr) is not None) for attr in ['_pool', 'artist', 'illust', 'post'])


def AppendKey(notation):
    return next((key, getattr(notation, key)) for (attr, key) in APPEND_KEY_DICT.items() if (getattr(notation, attr) is not None))
