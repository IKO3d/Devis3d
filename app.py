from flask import Flask, request, jsonify
from flask_cors import CORS
import trimesh
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # ✅ Autorise les requêtes Shopify
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Prix de base
BASE_PRICE = 10  # Prix minimum
PRICE_PER_MM3 = 0.02  # Prix par mm³

def calculate_volume(stl_path):
    try:
        mesh = trimesh.load_mesh(stl_path)
        return mesh.volume
    except Exception as e:
        print("Erreur d'analyse du fichier:", e)
        return None

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

    volume = calculate_volume(filepath)
    os.remove(filepath)  # Supprimer le fichier après analyse

    if volume is None:
        return jsonify({"error": "Impossible de calculer le volume"}), 500

    # Récupération des paramètres
    quality = request.form.get("quality", "standard")
    wall_thickness = float(request.form.get("wallThickness", 1.2))
    infill = float(request.form.get("infill", 20))

    # Calcul du prix
    price = BASE_PRICE + (volume * PRICE_PER_MM3)
    if quality == "avance":
        price += (wall_thickness * 2) + (infill / 10)

    return jsonify({"price": round(price, 2)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
