import re
import html
import datetime
from flask import Markup, request, render_template, url_for, Markup
from wtforms import Field, BooleanField, TextAreaField
from wtforms.widgets import HiddenInput

from ..logical.utility import TimeAgo

def RenderTemplate(*args, **kwargs):
    return Markup(render_template(*args, **kwargs))

def HasItems(items):
    return len(items) > 0

def Length(items):
    return len(items)

def FlashMessages(messages):
    return Markup('<br>----------------------------------<br>'.join(messages))

def SearchUrlFor(endpoint, **kwargs):
    def _Recurse(current_key, arg_dict, url_args):
        #print(current_key, arg_dict, url_args)
        for key in arg_dict:
            updated_key = current_key + '[' + key + ']'
            if type(arg_dict[key]) is dict:
                _Recurse(updated_key, arg_dict[key], url_args)
            else:
                url_args[updated_key] = arg_dict[key]
    url_args = {}
    _Recurse('search', kwargs, url_args)
    #print("Final:", url_args)
    return url_for(endpoint, **url_args)

def ConvertStrToHTML(text):
    return Markup(re.sub('\r?\n', '<br>', html.escape(text)))


def StrOrNone(val):
    return Markup('<em>none</em>') if val is None else val

def FormatTimestamp(timeval):
    return datetime.datetime.isoformat(timeval) if timeval is not None else Markup('<em>none</em>')

def FormatTimestamps(item):
    text = FormatTimestamp(item.created)
    delta = item.updated - item.created
    print(delta)
    if delta.days > 0 or delta.seconds > 3600:
        text += " ( %s )" % TimeAgo(item.updated)
    return text

def NavLinkTo(text, endpoint):
    link_blueprint = endpoint.split('.')[0]
    request_blueprint = request.endpoint.split('.')[0]
    klass = 'current' if link_blueprint == request_blueprint else None
    #print("#0", repr(klass), repr(endpoint), repr(request.endpoint))
    html_text = text.lower().replace(" ", "-")
    return Markup(render_template("layouts/_nav_link.html", text=text, html_text=html_text, endpoint=endpoint, klass=klass))

def SubnavLinkTo(text, endpoint, id=None, attrs={}, **kwargs):
    html_text = text.lower().replace(" ", "-")
    return Markup(render_template("layouts/_subnav_link.html", text=text, html_text=html_text, endpoint=endpoint, id=id, attrs=attrs, kwargs=kwargs))

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
    return RenderTemplate("layouts/_paginator.html", prev_page=previous_page, current_page=current_page, next_page=next_page, pages=pages)

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

def DescriptionText(description):
    return Markup('<small style="font-size: 80%; color: #888; font-style: italic;">' + description + '</small>')

def AddContainer(tagname, markup_text, classlist=[], **attrs):
    class_string = ' class="%s"' % ' '.join(classlist) if len(classlist) > 0 else ''
    attr_string = ' ' + ' '.join(['%s="%s"' % attr for attr in attrs.items()]) if len(attrs) else ''
    return Markup('<%s%s%s>' % (tagname, class_string, attr_string)) + markup_text + Markup('</%s>' % tagname)

def FormIterator(form):
    form_fields = [attr for attr in dir(form) if not attr.startswith('__') and issubclass(getattr(form, attr).__class__, Field)]
    for field in form:
        field_name = next(filter(lambda x: getattr(form, x) == field, form_fields))
        def _builder(**kwargs):
            nonlocal field
            if type(field) is BooleanField:
                built_markup = str(field.label) + field(value="1") + field(value="0", type="hidden")
            elif type(field.widget) is HiddenInput:
                return AddContainer('div', str(field), classlist=['input', 'hidden']) if field.data is not None else ""
            else:
                built_markup = str(field.label)
                if 'onclick' in kwargs:
                    built_markup += field(onclick=kwargs['onclick'])
                else:
                    built_markup += field
            description = kwargs['description'] if 'description' in kwargs else field.description
            if description:
                built_markup += DescriptionText(description)
            classlist = ['input'] + kwargs['classlist'] if 'classlist' in kwargs else []
            return AddContainer('div', built_markup, classlist=classlist)
        yield field_name, _builder

def HasErrorMessages(messages):
    return any((category, message) for (category, message) in messages if category == 'error')

def UrlLink(url):
    return Markup('<a href="%s">%s</a>' % (url, url))
