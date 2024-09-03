from dotenv import load_dotenv
import os
import json
import requests
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

CORS(app, resources={r"/*": {"origins": [frontend_url, "https://control-personal-sucesores.vercel.app"]}})

# Configuración para Dropbox
DROPBOX_CLIENT_ID = os.getenv('DROPBOX_CLIENT_ID')
DROPBOX_CLIENT_SECRET = os.getenv('DROPBOX_CLIENT_SECRET')
DROPBOX_PATH = '/data.xlsx'
REFRESH_TOKEN_FILE = 'refresh_token.json'

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_refresh_token():
    # Intentar obtener el token de refresco actual
    if os.path.exists(REFRESH_TOKEN_FILE):
        with open(REFRESH_TOKEN_FILE, 'r') as file:
            data = json.load(file)
            return data.get('refresh_token')
    return None

def get_access_token():
    # Intentar obtener el token de acceso actual
    if os.path.exists(REFRESH_TOKEN_FILE):
        with open(REFRESH_TOKEN_FILE, 'r') as file:
            data = json.load(file)
            return data.get('access_token')
    return None

def save_refresh_token(token, access_token=None):
    with open(REFRESH_TOKEN_FILE, 'w') as file:
        json.dump({
            'refresh_token': token,
            'access_token': access_token
        }, file)

def refresh_dropbox_token():
    refresh_token = get_refresh_token()
    if not refresh_token:
        raise Exception('Refresh token not found')
    
    try:
        response = requests.post(
            'https://api.dropboxapi.com/oauth2/token',
            data={
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': DROPBOX_CLIENT_ID,
                'client_secret': DROPBOX_CLIENT_SECRET
            }
        )
        response.raise_for_status()
        tokens = response.json()
        access_token = tokens['access_token']
        save_refresh_token(refresh_token, access_token)
        return access_token
    except Exception as e:
        print(f'Error refreshing Dropbox token: {e}')
        raise

# Inicializar el cliente de Dropbox
access_token = get_access_token()
if not access_token:
    access_token = refresh_dropbox_token()
dropbox_client = dropbox.Dropbox(access_token)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit-form', methods=['POST'])
def submit_form():
    try:
        data = request.json

        # Intentar descargar el archivo desde Dropbox
        try:
            try:
                metadata, file_content = dropbox_client.files_download(DROPBOX_PATH)
                existing_df = pd.read_excel(file_content.content)
            except dropbox.exceptions.ApiError as e:
                if e.error.is_path() and e.error.get_path().is_conflict():
                    return jsonify({"error": "Conflicto al descargar el archivo"}), 500
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

        except dropbox.exceptions.AuthError as e:
            # Si el token está caducado, intentar refrescarlo
            if 'Invalid access token' in str(e):
                access_token = refresh_dropbox_token()
                dropbox_client = dropbox.Dropbox(access_token)
                # Reintentar la operación
                return submit_form()

        except Exception as e:
            return jsonify({"error": str(e)}), 500

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
