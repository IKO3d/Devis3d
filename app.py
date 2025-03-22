from flask import Flask, request, jsonify
from flask_cors import CORS
import trimesh
import os
import numpy as np
from werkzeug.utils import secure_filename

def calculate_price(volume, material, infill):
    base_price = (2.4910 * np.log(volume) - 16.04) * 1.10
    if material == "PETG":
        base_price *= 1.15
    if infill > 20:
        base_price *= 1 + (0.05 * ((infill - 20) // 10))
    return max(2, round(base_price, 2))

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

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

    material = request.form.get("material", "PLA")
    try:
        infill = int(request.form.get("infill", 20))
    except ValueError:
        return jsonify({"error": "Remplissage invalide"}), 400

    try:
        mesh = trimesh.load_mesh(filepath)
        volume = mesh.volume
    except Exception as e:
        return jsonify({"error": "Erreur analyse STL", "details": str(e)}), 500
    finally:
        os.remove(filepath)

    price = calculate_price(volume, material, infill)
    return jsonify({"price": price})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

