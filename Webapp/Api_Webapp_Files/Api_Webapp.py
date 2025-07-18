import os 
from flask import Flask, render_template, send_from_directory
from Api_Webapp_Home_Page import Api_Webapp_Home_Page
from Api_Webapp_Wikipedia_Pages import Api_Webapp_Wikipedia_Pages
from Api_Webapp_Rag_Using_Page import Api_Webapp_Rag_Using_Page

IN_DOCKER = os.environ.get('IN_DOCKER', False)

# Configuration des URLs
URL_API_WEBAPP = "0.0.0.0" if IN_DOCKER else "127.0.0.1"
URL_API_MODEL = "model" if IN_DOCKER else "0.0.0.0"
PORT_API_WEBAPP = 5000
PORT_API_MODEL = 5001

# Définir les chemins absolus vers les dossiers 'Templates' et 'Static'
template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Templates')
static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Static')

# Crée l'application Flask en spécifiant les chemins
App = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

# Enregistrer le Blueprint
App.register_blueprint(Api_Webapp_Home_Page, url_prefix='/')
App.register_blueprint(Api_Webapp_Wikipedia_Pages, url_prefix='/Wikipedia_Pages')
App.register_blueprint(Api_Webapp_Rag_Using_Page, url_prefix='/Rag_Using_Page')

# Route personnalisée pour servir les fichiers statiques depuis le dossier 'Static'
@App.route('/Static/<path:filename>')
def serve_static(filename):
    return send_from_directory(App.static_folder, filename)

if __name__ == '__main__':
    App.run(host=URL_API_WEBAPP, port=PORT_API_WEBAPP, debug=True)