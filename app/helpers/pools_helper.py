# APP\HELPERS\POOLS_HELPER.PY

# ## PYTHON IMPORTS
from flask import render_template


# ## FUNCTIONS

def DisplayArtists(artist_ids):
    if len(artist_ids) == 0:
        return "<em>No artists.</em>"
    return render_template("pools/_artist_list.html", artist_ids=artist_ids)


def DisplayIllusts(illust_ids):
    if len(illust_ids) == 0:
        return "<em>No illusts.</em>"
    return render_template("pools/_illust_list.html", illust_ids=illust_ids)


def ItemIsOfType(item, type):
    return item.__table__.name == type


def ItemIsOfTypes(item, types):
    return any(map(lambda x: ItemIsOfType(item, x), types))


def MediaHeader(item):
    if ItemIsOfType(item, 'illust'):
        return item.type.title() + ':'
    if ItemIsOfType(item, 'post'):
        return ('Video' if item.file_ext in ['mp4'] else 'Image') + ':'
    return ""


def IsGeneralForm(form):
    return (form.illust_id.data is None) and (form.post_id.data is None) and (form.notation_id.data is None)
