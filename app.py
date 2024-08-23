import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd

# Crear la instancia de Flask
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app, origins=["https://frontend-taupe-tau.vercel.app"])

# Ruta a la carpeta compartida en red
DATA_DIR = r'\\192.168.0.251\artemis\Control de Calidad\2. Control de Personal\PERSONAL 2024'
DATA_FILE = os.path.join(DATA_DIR, 'data.xlsx')

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit-form', methods=['POST'])
def submit_form():
    try:
        data = request.json

        df = pd.DataFrame([{
            'Fecha': data['fecha'],
            'Turno': data['turno'],
            'Área': data['area'],
            'Nombre del Operario': data['nombre_operario'],
            'Manos Limpias': data['manos_limpias'],
            'Uniforme Limpio': data['uniforme_limpio'],
            'No Objetos Personales': data['no_objetos_personales'],
            'Heridas Protegidas': data['heridas_protegidas'],
            'Cofia Bien Puesta': data['cofia_bien_puesta'],
            'Mascarilla Bien Colocada': data['mascarilla_bien_colocada'],
            'Protector Auditivo': data['protector_auditivo'],
            'Uñas Cortas': data['unas_cortas'],
            'Guantes en Buen Estado': data['guantes_limpios'],
            'Pestañas': data['pestanas'],
            'Barba/Bigote': data['barba_bigote'],
            'Medicamento Autorizado': data['medicamento_autorizado'],
            'Supervisor': data['supervisor'],
            'Observaciones': data['observaciones']
        }])

        try:
            existing_df = pd.read_excel(DATA_FILE)
            df = pd.concat([existing_df, df], ignore_index=True)
        except FileNotFoundError:
            pass

        df.to_excel(DATA_FILE, index=False)

        return jsonify({"message": "Datos guardados con éxito"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Configuración para producción
    app.run(host='0.0.0.0', port=5000, debug=False)
