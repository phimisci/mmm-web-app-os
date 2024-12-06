# Copyright (c) 2024 Thomas Jurczyk
# This software is provided under the MIT License.
# For more information, please refer to the LICENSE file in the root directory of this project.

from flask import Blueprint

auth = Blueprint("auth", __name__, url_prefix='/auth')

from . import routes