from flask import Blueprint, request, jsonify, render_template, send_from_directory
import os

Api_Webapp_Wikipedia_Pages = Blueprint('Api_Webapp_Wikipedia_Pages', __name__, url_prefix='/Wikipedia_Pages')

WIKIPEDIA_DATA_PATH = os.path.join("Data")

@Api_Webapp_Wikipedia_Pages.route('/')
def Home_Page_Wikipedia_Pages():
    return render_template('Wikipedia_Pages.html')


@Api_Webapp_Wikipedia_Pages.route('/list_files')
def list_files():
    """
    Retourne la liste des fichiers .txt disponibles dans le dossier Data/
    """
    try:
        files = [f for f in os.listdir(WIKIPEDIA_DATA_PATH) if f.endswith(".txt")]
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

from flask import send_file
import os

@Api_Webapp_Wikipedia_Pages.route('/get_file/<path:filename>')
def get_file(filename):
    """
    Retourne le contenu d’un fichier texte depuis le dossier Data.
    """
    try:
        # Construction du chemin absolu
        full_path = os.path.abspath(os.path.join(WIKIPEDIA_DATA_PATH, filename))
        print(f"✅ Envoi du fichier : {full_path}")

        # Vérification d'existence manuelle (optionnelle)
        if not os.path.isfile(full_path):
            raise FileNotFoundError(f"Fichier introuvable: {full_path}")

        return send_file(full_path, mimetype='text/plain')
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return jsonify({"error": str(e)}), 404
