from flask import Blueprint

maker = Blueprint("maker", __name__, url_prefix='/maker')

from . import routes