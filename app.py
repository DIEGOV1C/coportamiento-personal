from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError
from supabase import create_client, Client

# Cargar las variables de entorno
load_dotenv()

# Crear la instancia de Flask
app = Flask(__name__, static_folder='static', template_folder='templates')
frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:8080')

CORS(app, resources={r"/*": {"origins": frontend_url}})

# Configuración para Dropbox
DROPBOX_TOKEN = os.getenv('DROPBOX_TOKEN')
DROPBOX_PATH = '/data.xlsx'
dropbox_client = dropbox.Dropbox(DROPBOX_TOKEN)

# Configuración para la base de datos
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit-form', methods=['POST'])
def submit_form():
    try:
        data = request.json

        # Descargar el archivo desde Dropbox
        try:
            metadata, file_content = dropbox_client.files_download(DROPBOX_PATH)
            existing_df = pd.read_excel(file_content.content)
        except dropbox.exceptions.ApiError as e:
            if e.error.is_path() and e.error.get_path().is_conflict():
                return jsonify({"error": "Conflicto al descargar el archivo"}), 500
            # Crear un DataFrame vacío si el archivo no existe
            existing_df = pd.DataFrame()

        # Agregar el nuevo registro
        new_record = pd.DataFrame([{
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
        df = pd.concat([existing_df, new_record], ignore_index=True)

        # Guardar el DataFrame actualizado en un archivo Excel temporal
        temp_file = 'temp_data.xlsx'
        df.to_excel(temp_file, index=False)

        # Subir el archivo actualizado a Dropbox
        with open(temp_file, 'rb') as f:
            dropbox_client.files_upload(f.read(), DROPBOX_PATH, mode=WriteMode('overwrite'))

        # Eliminar el archivo temporal
        os.remove(temp_file)

        return jsonify({"message": "Datos guardados con éxito"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get-personnel', methods=['GET'])
def get_personnel():
    try:
        # Consultar la base de datos
        response = supabase.table('personnel').select('*').execute()
        data = response.data

        return jsonify({"personnel": data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get-areas', methods=['GET'])
def get_areas():
    try:
        # Consultar la base de datos
        response = supabase.table('area').select('*').execute()
        data = response.data

        return jsonify({"areas": data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=os.getenv('DEBUG', 'False') == 'True')
