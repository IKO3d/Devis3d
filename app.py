from flask import Flask, request, jsonify
from flask_cors import CORS
import trimesh
import os
import numpy as np
from werkzeug.utils import secure_filename

def calculate_price(volume, material, infill):
    """
    Calcule le prix basé sur la nouvelle formule ajustée avec :
    - Augmentation de 10%
    - Choix du matériau (PETG +15%)
    - Remplissage : +5% du prix par tranche de 10% d'infill au-delà de 20%
    """
    base_price = (2.4910 * np.log(volume) - 16.04) * 1.10  # Augmentation de 10%
    
    # Ajustement selon le matériau
    if material == "PETG":
        base_price *= 1.15  # PETG +15%
    
    # Ajustement selon le remplissage (chaque 10% au-dessus de 20% ajoute +5% au prix)
    if infill > 20:
        base_price *= 1 + (0.05 * ((infill - 20) // 10))
    
    return max(2, round(base_price, 2))  # Applique un prix minimum de 2€

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

    # Récupération des paramètres optionnels avec sécurisation
    material = request.form.get("material", "PLA")  # Par défaut PLA
    try:
        infill = int(request.form.get("infill", 20))  # Par défaut 20%
    except ValueError:
        return jsonify({"error": "Valeur incorrecte pour le remplissage"}), 400

    print(f"Matériau reçu: {material}")
    print(f"Remplissage reçu: {infill}")

    try:
        mesh = trimesh.load_mesh(filepath)
        volume = mesh.volume
    except Exception as e:
        return jsonify({"error": "Impossible d'analyser le fichier STL", "details": str(e)}), 500
    finally:
        os.remove(filepath)

    price = calculate_price(volume, material, infill)
    return jsonify({"price": price})  # Réponse en JSON lisible par Shopify

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
