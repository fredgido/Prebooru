import re
import html
from flask import Markup, render_template

from .base_helper import ConvertStrToHTML

HTTP_RG = re.compile(r'(\b(?:http|https)(?::\/{2}[\w]+)(?:[\/|\.]?)(?:[^\s<>\uff08\uff09\u3011\u3000"\[\]]*))',re.ASCII)

def DisplayNotes(item):
    if len(item.notations) == 0:
        return ""
    return render_template("notations/_list.html", notations=item.notations)

def Excerpt(notation):
    lines = re.split(r'\r?\n', notation.body)
    return ConvertStrToHTML(lines[0][:50] + ('...' if len(lines[0]) > 50 else ''))

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

def IsGeneralForm(form):
    return (form.pool_id.data is None) and (form.artist_id.data is None) and (form.illust_id.data is None) and (form.post_id.data is None)