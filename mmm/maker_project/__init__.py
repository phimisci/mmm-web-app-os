# Copyright (c) 2024 Thomas Jurczyk
# This software is provided under the MIT License.
# For more information, please refer to the LICENSE file in the root directory of this project.

from flask import Blueprint

maker_project = Blueprint("maker_project", __name__, url_prefix='/maker-project')

from . import routes