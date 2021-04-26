# PREBOORU.PY

# ## LOCAL IMPORTS
from app import app
from app.controllers import uploads, posts, illusts, artists


# ### INITIALIZATION

app.register_blueprint(illusts.bp)
app.register_blueprint(artists.bp)
app.register_blueprint(uploads.bp)
app.register_blueprint(posts.bp)


# ##EXECUTION START

if __name__ == '__main__':
    app.run(threaded=True)
