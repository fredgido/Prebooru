import datetime
from flask import Markup, request, render_template


def StrOrNone(val):
    return Markup('<em>none</em>') if val is None else val

def FormatTimestamp(timeval):
    return datetime.datetime.isoformat(timeval)


def NavLinkTo(text, endpoint):
    klass = 'current' if request.endpoint == endpoint else None
    print("#0", repr(klass), repr(endpoint), repr(request.endpoint))
    html_text = text.lower().replace(" ", "-")
    return Markup(render_template("layouts/_nav_link.html", text=text, html_text=html_text, endpoint=endpoint, klass=klass))


def PageNavigation(paginate):
    print(request.endpoint)
    current_page = paginate.page
    previous_page = paginate.prev_num
    next_page = paginate.next_num
    last_page = paginate.pages
    left = max(current_page - 4, 2)
    penultimate_page = last_page - 1
    right = min(current_page + 4, penultimate_page)
    pages = [1]
    pages += ['...'] if left != 2 else []
    pages += list(range(left, right))
    pages += ['...'] if right != penultimate_page else []
    pages += [last_page] if last_page != 1 else []
    return render_template("layouts/_paginator.html", prev_page=previous_page, current_page=current_page, next_page=next_page, pages=pages)
