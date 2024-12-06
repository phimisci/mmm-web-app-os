# Copyright (c) 2024 Thomas Jurczyk
# This software is provided under the MIT License.
# For more information, please refer to the LICENSE file in the root directory of this project.

from flask import request, render_template, Blueprint
from flask_login import login_required
import os
from markdown import markdown

main = Blueprint("main", __name__)

## INDEX ROUTE
@main.route("/", methods=['GET'])
def index():
    if request.method == "GET":
        # Get custom imprint data from file in custom folder
        # If file does not exist, return default imprint page
        if os.path.exists("mmm/custom/main.md"):
            with open("mmm/custom/main.md", "r") as file:
                content = markdown(file.read())
                # Render imprint page with custom content
                return render_template("index.html", content=content)
        # Default imprint page
        return render_template("index.html", content="No file custom/main.md found.")
    
## ABOUT ROUTE
@main.route("/about", methods=['GET'])
def about():
    if request.method == "GET":
        return render_template("about.html")
    
## IMPRINT ROUTE
@main.route("/imprint", methods=['GET'])
def imprint():
    if request.method == "GET":
        # Get custom imprint data from file in custom folder
        # If file does not exist, return default imprint page
        if os.path.exists("mmm/custom/imprint.md"):
            with open("mmm/custom/imprint.md", "r") as file:
                content = markdown(file.read())
                # Render imprint page with custom content
                return render_template("imprint.html", content=content)
        # Default imprint page
        return render_template("imprint.html", content="No file custom/imprint.md found.")
        
## VERSION ROUTE
@main.route("/version", methods=['GET'])
def version():
	if request.method == "GET":
		return render_template("version-info.html")
     
## SELECTION
@main.route("/select-maker", methods=["GET"])
@login_required
def select_maker():
     if request.method == "GET":
          return render_template("select-maker.html")