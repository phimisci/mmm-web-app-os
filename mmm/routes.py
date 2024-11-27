from flask import request, render_template, Blueprint
from flask_login import login_required

main = Blueprint("main", __name__)

## INDEX ROUTE
@main.route("/", methods=['GET'])
def index():
    if request.method == "GET":
        return render_template("index.html")
    
## ABOUT ROUTE
@main.route("/about", methods=['GET'])
def about():
    if request.method == "GET":
        return render_template("about.html")
    
## IMPRINT ROUTE
@main.route("/imprint", methods=['GET'])
def imprint():
    if request.method == "GET":
        return render_template("imprint.html")
    
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