# APP/HELPERS/NOTATIONS_HELPERS.PY

# ##PYTHON IMPORTS
import re
import html
from flask import Markup

# ##LOCAL IMPORTS
from .base_helper import ConvertStrToHTML


# ##GLOBAL VARIABLES


HTTP_RG = re.compile(r'(\b(?:http|https)(?::\/{2}[\w]+)(?:[\/|\.]?)(?:[^\s<>\uff08\uff09\u3011\u3000"\[\]]*))', re.ASCII)


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


# ###### NEW/EDIT


def FormTitle(form):
    if form.pool_id.data:
        return "for pool #%d" % form.pool_id.data
    if form.artist_id.data:
        return "for artist #%d" % form.artist_id.data
    if form.illust_id.data:
        return "for illust #%d" % form.illust_id.data
    if form.post_id.data:
        return "for post #%d" % form.post_id.data


def FormHeader(form):
    html_text = "notation"
    if IsGeneralForm(form):
        return html_text
    html_text += ': '
    if form.pool_id.data:
        html_text += """<a href="{{ url_for('pool.show_html_text', id=%d) }}">pool #%d</a>""" % (form.pool_id.data, form.pool_id.data)
    elif form.artist_id.data:
        html_text += """<a href="{{ url_for('artist.show_html_text', id=%d) }}">artist #%d</a>""" % (form.artist_id.data, form.artist_id.data)
    elif form.illust_id.data:
        html_text += """<a href="{{ url_for('illust.show_html_text', id=%d) }}">illust #%d</a>""" % (form.illust_id.data, form.illust_id.data)
    elif form.post_id.data:
        html_text += """<a href="{{ url_for('post.show_html_text', id=%d) }}">post #%d</a>""" % (form.post_id.data, form.post_id.data)
    return Markup(html_text)
