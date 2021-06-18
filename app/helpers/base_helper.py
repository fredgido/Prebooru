import re
import html
import datetime
from flask import Markup, request, render_template, url_for, Markup

def HasItems(items):
    return len(items) > 0

def SearchUrlFor(endpoint, **kwargs):
    def _Recurse(current_key, arg_dict, url_args):
        print(current_key, arg_dict, url_args)
        for key in arg_dict:
            updated_key = current_key + '[' + key + ']'
            if type(arg_dict[key]) is dict:
                _Recurse(updated_key, arg_dict[key], url_args)
            else:
                url_args[updated_key] = arg_dict[key]
    url_args = {}
    _Recurse('search', kwargs, url_args)
    print("Final:", url_args)
    return url_for(endpoint, **url_args)

def ConvertStrToHTML(text):
    return Markup(re.sub('\r?\n', '<br>', html.escape(text)))


def StrOrNone(val):
    return Markup('<em>none</em>') if val is None else val

def FormatTimestamp(timeval):
    return datetime.datetime.isoformat(timeval) if timeval is not None else Markup('<em>none</em>')


def NavLinkTo(text, endpoint):
    link_blueprint = endpoint.split('.')[0]
    request_blueprint = request.endpoint.split('.')[0]
    klass = 'current' if link_blueprint == request_blueprint else None
    #print("#0", repr(klass), repr(endpoint), repr(request.endpoint))
    html_text = text.lower().replace(" ", "-")
    return Markup(render_template("layouts/_nav_link.html", text=text, html_text=html_text, endpoint=endpoint, klass=klass))

def SubnavLinkTo(text, endpoint, id=None):
    html_text = text.lower().replace(" ", "-")
    return Markup(render_template("layouts/_subnav_link.html", text=text, html_text=html_text, endpoint=endpoint, id=id))

def PageNavigation(paginate):
    #print("PageNavigation-1:", paginate.page, paginate.prev_num, paginate.next_num, paginate.pages)
    current_page = paginate.page
    previous_page = paginate.prev_num
    next_page = paginate.next_num
    last_page = paginate.pages
    left = max(current_page - 4, 2)
    penultimate_page = last_page - 1
    right = min(current_page + 4, penultimate_page)
    pages = [1]
    pages += ['...'] if left != 2 else []
    pages += list(range(left, right+1))
    pages += ['...'] if right != penultimate_page else []
    pages += [last_page] if last_page > 1 else []
    #print("PageNavigation-2:", previous_page, current_page, next_page, pages, left, right, last_page, penultimate_page)
    return render_template("layouts/_paginator.html", prev_page=previous_page, current_page=current_page, next_page=next_page, pages=pages)

def UrlForWithArgs(endpoint, **kwargs):
    url_args = {}
    for arg in kwargs:
        url_args[arg] = kwargs[arg]
    for arg in request.args:
        if arg not in kwargs:
            url_args[arg] = request.args[arg]
    if request.endpoint.find('.show_html') >= 0:
        url_args['id'] = int(re.search(r'\d+$', request.path).group(0))
    return url_for(endpoint, **url_args)

