from flask import Flask, request, jsonify
from flask_cors import CORS
import trimesh
import os
import numpy as np
from werkzeug.utils import secure_filename

def calculate_price(volume):
    """
    Calcule le prix basé sur la nouvelle formule ajustée pour Shopify.
    Prix (€) = max(2, 2.4910 * log(Volume) - 16.04)
    """
    price = (2.4910 * np.log(volume) - 16.04) * 1.10  # Augmentation de 10%
    return max(2, round(price, 2))  # Applique un prix minimum de 2€

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Permet à Shopify d'accéder à l'API

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/analyse-stl', methods=['POST'])
def analyse_stl():
    if 'stlFile' not in request.files:
        return jsonify({"error": "Aucun fichier reçu"}), 400

    file = request.files['stlFile']
    if file.filename == '':
        return jsonify({"error": "Fichier invalide"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        mesh = trimesh.load_mesh(filepath)
        volume = mesh.volume
    except Exception as e:
        return jsonify({"error": "Impossible d'analyser le fichier STL", "details": str(e)}), 500
    finally:
        os.remove(filepath)

    price = calculate_price(volume)
    return jsonify({"price": price})  # Réponse en JSON lisible par Shopify

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
