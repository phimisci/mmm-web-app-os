from flask import Blueprint

maker_project = Blueprint("maker_project", __name__, url_prefix='/maker-project')

from . import routes