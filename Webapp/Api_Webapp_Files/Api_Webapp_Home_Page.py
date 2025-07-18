from flask import Blueprint, request, jsonify, render_template
import sys
import requests 
import os

PATH_MODULES = "Modules/"
sys.path.append(PATH_MODULES)

PATH_MODELS = "Models/"
sys.path.append(PATH_MODELS)

Api_Webapp_Home_Page = Blueprint('Api_Webapp_Home_Page', __name__, url_prefix='/')

IN_DOCKER = os.environ.get('IN_DOCKER', False)

# Configuration des URLs
URL_API_WEBAPP = "0.0.0.0" if IN_DOCKER else "127.0.0.1"
URL_API_MODEL = "model" if IN_DOCKER else "0.0.0.0"
PORT_API_WEBAPP = 5000
PORT_API_MODEL = 5001

@Api_Webapp_Home_Page.route('/')
def Home_Page():
    """
    Route for the home page of the web application.
    """
    return render_template('Home_Page.html')

