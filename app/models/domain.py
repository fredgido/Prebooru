# APP/CACHE/DOMAIN.PY

# ##LOCAL IMPORTS
from app import DB


# ## CLASSES

class Domain(DB.Model):
    # ## Declarations

    # #### SqlAlchemy

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.String(255), nullable=False)
    redirector = DB.Column(DB.Boolean, nullable=False)
