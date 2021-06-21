# APP\CONTROLLERS\PROXY_CONTROLLER.PY

# ## PYTHON IMPORTS
import requests
from bs4 import BeautifulSoup
from flask import Blueprint, request, render_template, abort, Markup

# ## LOCAL IMPORTS
from ..logical.file import PutGetRaw
from ..sources import base as BASE_SOURCE
from ..models import Post
from ..config import DANBOORU_USERNAME, DANBOORU_APIKEY

bp = Blueprint("proxy", __name__)

@bp.route('/proxy/danbooru_upload', methods=['GET'])
def danbooru_upload():
    post_id = request.args.get('post_id', type=int)
    if post_id is None:
        return "Must include post ID."
    post = Post.find(post_id)
    if post is None:
        return "Post #d not found." % post_id
    if len(post.illusts) > 1:
        illust_id = request.args.get('illust_id', type=int)
        if illust_id is None:
            return "Ambiguous illustrations. Must include illust ID."
        illust = next(filter(lambda x: x.id == illust_id, post.illusts), None)
        if illust is None:
            return "Illust #%d not on post #%d." % (post_id, illust_id)
    else:
        illust = post.illusts[0]
    source = BASE_SOURCE._Source(illust.site_id)
    post_url = source.GetPostUrl(illust)
    params = {
        'tag_string': 'source:' + post_url,
    }
    if len(illust.descriptions[0].body):
        params['artist_commentary_title'] = illust.descriptions[0].body
    #return params
    resp = requests.get('https://danbooru.donmai.us/uploads/new', params=params, auth=(DANBOORU_USERNAME, DANBOORU_APIKEY))
    if resp.status_code != 200:
        return "HTTP Error %d: %s" % (resp.status_code, resp.reason)
    soup = BeautifulSoup(resp.text, 'lxml')
    base = soup.new_tag("base")
    base['href'] = 'https://danbooru.donmai.us'
    soup.head.insert(0, base)
    if len(illust.descriptions[0].body):
        try:
            soup.select('.artist-commentary')[0]['style'] = None
        except Exception:
            pass
    return Markup(soup.prettify())

@bp.route('/proxy/danbooru_iqdb', methods=['GET'])
def danbooru_iqdb():
    post_id = request.args.get('post_id', type=int)
    if post_id is None:
        return "Must include post ID."
    post = Post.find(post_id)
    if post is None:
        return "Post #d not found." % post_id
    buffer = PutGetRaw(post.file_path, 'rb')
    files = {
        'search[file]': buffer,
    }
    resp = requests.post('https://danbooru.donmai.us/iqdb_queries', files=files, auth=(DANBOORU_USERNAME, DANBOORU_APIKEY))
    if resp.status_code != 200:
        return "HTTP Error %d: %s" % (resp.status_code, resp.reason)
    soup = BeautifulSoup(resp.text, 'lxml')
    base = soup.new_tag("base")
    base['href'] = 'https://danbooru.donmai.us'
    soup.head.insert(0, base)
    return Markup(soup.prettify())

@bp.route('/proxy/saucenao', methods=['GET'])
def saucenao():
    post_id = request.args.get('post_id', type=int)
    if post_id is None:
        return "Must include post ID."
    post = Post.find(post_id)
    if post is None:
        return "Post #d not found." % post_id
    buffer = PutGetRaw(post.file_path, 'rb')
    files = {
        'file': buffer,
    }
    resp = requests.post('https://saucenao.com/search.php', files=files)
    if resp.status_code != 200:
        return "HTTP Error %d: %s" % (resp.status_code, resp.reason)
    soup = BeautifulSoup(resp.text, 'lxml')
    base = soup.new_tag("base")
    base['href'] = 'https://saucenao.com'
    soup.head.insert(0, base)
    return Markup(soup.prettify())

@bp.route('/proxy/ascii2d', methods=['GET'])
def ascii2d():
    post_id = request.args.get('post_id', type=int)
    if post_id is None:
        return "Must include post ID."
    post = Post.find(post_id)
    if post is None:
        return "Post #d not found." % post_id
    buffer = PutGetRaw(post.file_path, 'rb')
    files = {
        'file': buffer,
    }
    resp = requests.post('https://ascii2d.net/search/file', files=files)
    if resp.status_code != 200:
        return "HTTP Error %d: %s" % (resp.status_code, resp.reason)
    soup = BeautifulSoup(resp.text, 'lxml')
    base = soup.new_tag("base")
    base['href'] = 'https://ascii2d.net'
    soup.head.insert(0, base)
    return Markup(soup.prettify())
