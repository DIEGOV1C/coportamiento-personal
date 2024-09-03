from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError
from supabase import create_client, Client
import requests

# Cargar las variables de entorno
load_dotenv()

# Crear la instancia de Flask
app = Flask(__name__, static_folder='static', template_folder='templates')
frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:8080')

CORS(app, resources={r"/*": {"origins": [frontend_url, "https://control-personal-sucesores.vercel.app"]}})

# Configuración para Dropbox
DROPBOX_ACCESS_TOKEN = os.getenv('DROPBOX_ACCESS_TOKEN')
DROPBOX_REFRESH_TOKEN = os.getenv('DROPBOX_REFRESH_TOKEN')
DROPBOX_PATH = '/data.xlsx'
DROPBOX_APP_KEY = os.getenv('DROPBOX_APP_KEY')
DROPBOX_APP_SECRET = os.getenv('DROPBOX_APP_SECRET')
dropbox_client = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# Configuración para la base de datos
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def refresh_dropbox_token():
    response = requests.post('https://api.dropboxapi.com/oauth2/token', data={
        'grant_type': 'refresh_token',
        'refresh_token': DROPBOX_REFRESH_TOKEN,
        'client_id': DROPBOX_APP_KEY,
        'client_secret': DROPBOX_APP_SECRET
    })
    response_data = response.json()
    new_access_token = response_data.get('access_token')
    new_refresh_token = response_data.get('refresh_token', DROPBOX_REFRESH_TOKEN)  # refresh_token might not be returned

    if new_access_token:
        # Actualiza el access token en la variable de entorno o almacenamiento seguro
        global DROPBOX_ACCESS_TOKEN
        DROPBOX_ACCESS_TOKEN = new_access_token
        dropbox_client = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    
    # Retorna el nuevo refresh token si está disponible
    return new_refresh_token

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
            elif e.user_message_text == 'Invalid access token':
                # Token expirado, intentar refrescarlo
                new_refresh_token = refresh_dropbox_token()
                # Guardar el nuevo refresh token
                # Aquí deberías guardar el nuevo refresh_token en un almacenamiento seguro, como una base de datos o archivo
                return jsonify({"error": "Token de acceso expirado. Inténtalo de nuevo."}), 401
            else:
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
