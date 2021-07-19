# APP\CONTROLLERS\PROXY_CONTROLLER.PY

# ## PYTHON IMPORTS
import requests
from bs4 import BeautifulSoup
from flask import Blueprint, request, render_template, abort, Markup, jsonify, redirect

# ## LOCAL IMPORTS
from ..logical.file import PutGetRaw
from ..sources import base as BASE_SOURCE
from ..models import Post
from .base_controller import GetDataParams
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
    if len(illust.commentaries[0].body):
        params['artist_commentary_title'] = illust.commentaries[0].body
    #return params
    resp = requests.get('https://danbooru.donmai.us/uploads/new', params=params, auth=(DANBOORU_USERNAME, DANBOORU_APIKEY))
    if resp.status_code != 200:
        return "HTTP Error %d: %s" % (resp.status_code, resp.reason)
    soup = BeautifulSoup(resp.content, 'lxml')
    base = soup.new_tag("base")
    #base['href'] = 'https://danbooru.donmai.us'
    base['href'] = 'http://127.0.0.1:2000/'
    soup.head.insert(0, base)
    if len(illust.commentaries[0].body):
        try:
            soup.select('.artist-commentary')[0]['style'] = None
        except Exception:
            pass
    for soup_tag in soup.select('[src^="/"]'):
        val = soup_tag['src']
        soup_tag['src'] = 'https://danbooru.donmai.us' + val
    for soup_tag in soup.select('[href^="/"]'):
        val = soup_tag['href']
        soup_tag['href'] = 'https://danbooru.donmai.us' + val
    return Markup(soup.prettify())

def _CORS_JSON(json):
    response = jsonify(json)
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

def ErrorResp(message):
    print("ErrorResp:", message)
    return _CORS_JSON({'error': True, 'message': message})

@bp.route('/proxy/danbooru_preprocess_upload.json', methods=['POST'])
def danbooru_preprocess_upload():
    post_id = request.values.get('post_id', type=int)
    if post_id is None:
        return ErrorResp("Must include post ID.")
    post = Post.find(post_id)
    if post is None:
        return ErrorResp("Post #d not found." % post_id)
    if len(post.illusts) > 1:
        illust_id = request.values.get('illust_id', type=int)
        if illust_id is None:
            return ErrorResp("Ambiguous illustrations. Must include illust ID.")
        illust = next(filter(lambda x: x.id == illust_id, post.illusts), None)
        if illust is None:
            return ErrorResp("Illust #%d not on post #%d." % (post_id, illust_id))
    else:
        illust = post.illusts[0]
    source = BASE_SOURCE._Source(illust.site_id)
    post_url = source.GetPostUrl(illust)
    profile_urls = source.ArtistProfileUrls(illust.artist)
    illust_commentaries = source.IllustCommentaries(illust)
    check = CheckPreprocess(post)
    if type(check) is str:
        return ErrorResp(check)
    if not check:
        preprocess = PreprocessPost(post)
        if type(preprocess) is str:
            return ErrorResp(preprocess)
    # NEED TO ADD BAD_ID/BAD_TWIITER_ID here for dead illusts
    return _CORS_JSON({'error': False, 'post_url': post_url, 'post': post.to_json(), 'profile_urls': profile_urls, 'illust_commentaries': illust_commentaries, 'illust': illust.to_json(), 'artist': illust.artist.to_json()})


@bp.route('/proxy/danbooru_create_upload.json', methods=['post'])
def danbooru_create_upload():
    dataparams = GetDataParams(request, 'upload')
    print("Data:", dataparams)
    return redirect('https://testbooru.donmai.us/uploads/new')

MIMETYPES = {
    'jpg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'mp4': 'video/mp4',
}

def CheckPreprocess(post):
    print("CheckPreprocess")
    params = {
        'search[uploader_name]': DANBOORU_USERNAME,
        'search[md5]': post.md5,
    }
    #print(params)
    danbooru_resp = requests.get('https://danbooru.donmai.us/uploads.json', params=params, auth=(DANBOORU_USERNAME, DANBOORU_APIKEY))
    #breakpoint()
    if danbooru_resp.status_code != 200:
        return "HTTP %d: %s; Unable to query Danbooru for existing upload: %s - %s" % (danbooru_resp.status_code, danbooru_resp.reason, DANBOORU_USERNAME, post.md5)
    data = danbooru_resp.json()
    print(data)
    return len(data)

def PreprocessPost(post):
    print("PreprocessPost")
    #return None
    buffer = PutGetRaw(post.file_path, 'rb')
    filename = post.md5 + '.' + post.file_ext
    mimetype = MIMETYPES[post.file_ext]
    files = {
        'upload[file]': (filename, buffer, mimetype)
    }
    try:
        #testbooru_resp = requests.post('https://testbooru.donmai.us/uploads/preprocess', files=files, auth=('BrokenEagle98', 'utvkhMWzJCHh8tJzED5wmdZq'), timeout=30)
        danbooru_resp = requests.post('https://danbooru.donmai.us/uploads/preprocess', files=files, auth=(DANBOORU_USERNAME, DANBOORU_APIKEY), timeout=30)
    except (requests.exceptions.ReadTimeout,requests.exceptions.ConnectionError) as e:
        return "Connection error: %s" % e
    if danbooru_resp.status_code != 200:
        return "HTTP %d - %s" % (danbooru_resp.status_code, danbooru_resp.reason)

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
    filename = post.md5 + '.' + post.file_ext
    files = {
        'file': (filename, buffer, 'application/octet-stream')
    }
    resp = requests.post('https://ascii2d.net/search/file', files=files)
    if resp.status_code != 200:
        return "HTTP Error %d: %s" % (resp.status_code, resp.reason)
    soup = BeautifulSoup(resp.text, 'lxml')
    base = soup.new_tag("base")
    base['href'] = 'https://ascii2d.net'
    soup.head.insert(0, base)
    return Markup(soup.prettify())
