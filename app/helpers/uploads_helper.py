# APP/HELPERS/UPLOADS_HELPER.PY

# ##PYTHON IMPORTS
from flask import Markup, url_for


# ## FUNCTIONS

def FormTitleApellation(illust_url):
    return Markup(': <a href="%s">illust #%d</a>' % (url_for('illust.show_html', id=illust_url.illust_id), illust_url.illust_id)) if illust_url is not None else ""
