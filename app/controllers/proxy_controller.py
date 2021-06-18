# APP\CONTROLLERS\PROXY_CONTROLLER.PY

# ## PYTHON IMPORTS
import requests
from flask import Blueprint, request, render_template, abort

bp = Blueprint("proxy", __name__)