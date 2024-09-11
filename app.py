from dotenv import load_dotenv
import os
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import pandas as pd
from supabase import create_client, Client
from io import BytesIO
from openpyxl import Workbook
import requests

# Cargar las variables de entorno
load_dotenv()

# Crear la instancia de Flask
app = Flask(__name__, static_folder='static', template_folder='templates')
frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:8080')

CORS(app, resources={r"/*": {"origins": ["https://control-personal-sucesores.vercel.app", frontend_url]}})


# Configuración de Supabase
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

        # Insertar los datos en la tabla "inspection" de Supabase
        response = supabase.table('inspection').insert({
            'fecha': data['fecha'],
            'turno': data['turno'],
            'area': data['area'],
            'nombre_operario': data['nombre_operario'],
            'manos_limpias': data['manos_limpias'],
            'uniforme_limpio': data['uniforme_limpio'],
            'no_objetos_personales': data['no_objetos_personales'],
            'heridas_protegidas': data['heridas_protegidas'],
            'cofia_bien_puesta': data['cofia_bien_puesta'],
            'mascarilla_bien_colocada': data['mascarilla_bien_colocada'],
            'protector_auditivo': data['protector_auditivo'],
            'unas_cortas': data['unas_cortas'],
            'guantes_limpios': data['guantes_limpios'],
            'pestanas': data['pestanas'],
            'barba_bigote': data['barba_bigote'],
            'medicamento_autorizado': data['medicamento_autorizado'],
            'supervisor': data['supervisor'],
            'observaciones': data['observaciones']
        }).execute()

        # Verificar si hubo algún error en la respuesta
        if response.data:
            return jsonify({"message": "Formulario guardado en la base de datos."}), 200
        else:
            return jsonify({"error": "Error al guardar en la base de datos"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download-inspection', methods=['GET'])
def download_inspection():
    try:
        # Obtener datos de la base de datos
        response = supabase.table('inspection').select("*").execute()
        data = response.data

        # Crear un libro de trabajo de Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "Inspecciones"

        # Agregar encabezados
        headers = ["Fecha", "Turno", "Área", "Nombre del operario", "Manos limpias", "Uniforme limpio", 
                   "No objetos personales", "Heridas protegidas", "Cofia bien puesta", 
                   "Mascarilla bien colocada", "Uso de protector auditivo", "Uñas cortas", 
                   "Guantes limpios", "Pestañas", "Barba/Bigote", "Medicamento autorizado", "Supervisor", "Observaciones"]
        ws.append(headers)

        # Agregar datos
        for record in data:
            row = [
                record.get("fecha"),
                record.get("turno"),
                record.get("area"),
                record.get("nombre_operario"),
                record.get("manos_limpias"),
                record.get("uniforme_limpio"),
                record.get("no_objetos_personales"),
                record.get("heridas_protegidas"),
                record.get("cofia_bien_puesta"),
                record.get("mascarilla_bien_colocada"),
                record.get("protector_auditivo"),
                record.get("unas_cortas"),
                record.get("guantes_limpios"),
                record.get("pestanas"),
                record.get("barba_bigote"),
                record.get("medicamento_autorizado"),
                record.get("supervisor"),
                record.get("observaciones")
            ]
            ws.append(row)

        # Guardar el archivo en un objeto BytesIO y enviarlo
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        return send_file(
            output,
            as_attachment=True,
            download_name="inspecciones.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get-personnel', methods=['GET'])
def get_personnel():
    try:
        # Consultar la base de datos el personal
        response = supabase.table('personnel').select('*').execute()
        data = response.data

        return jsonify({"personnel": data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get-areas', methods=['GET'])
def get_areas():
    try:
        # Consultar la base de datos las areas
        response = supabase.table('area').select('*').execute()
        data = response.data

        return jsonify({"areas": data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/get-roles', methods=['GET'])
def get_roles():
    try:
        # Consultar la base de datos y obtener cargos
        response = supabase.table('personnel').select('role').execute()
        data = response.data

        # Obtener los cargos
        roles = list(set(person['role'] for person in data if person['role']))

        return jsonify({"roles": roles}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/add-personnel', methods=['POST'])
def add_personnel():
    try:
        data = request.json
        response = supabase.table('personnel').insert({
            'name': data['name'],
            'role': data['role'],
            'id_area': data['id_area']
        }).execute()

        if response.data:
            return jsonify({"message": "Personal agregado con éxito."}), 200
        else:
            return jsonify({"error": "Error al agregar personal"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update-personnel', methods=['PUT'])
def update_personnel():
    try:
        data = request.json
        response = supabase.table('personnel').update({
            'name': data['name'],
            'role': data['role'],
            'id_area': data['id_area']
        }).eq('id', data['id']).execute()

        if response.data:
            return jsonify({"message": "Personal actualizado con éxito."}), 200
        else:
            return jsonify({"error": "Error al actualizar personal"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/delete-personnel/<id>', methods=['DELETE'])
def delete_personnel(id):
    try:
        response = supabase.table('personnel').delete().eq('id', id).execute()

        if response.data:
            return jsonify({"message": "Personal eliminado con éxito."}), 200
        else:
            return jsonify({"error": "Error al eliminar personal"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/inspection-frequency', methods=['GET'])
def get_inspection_frequency():
    try:
        # Llamada a la función almacenada de Supabase
        response = supabase.rpc('get_inspection_frequency').execute()

        # Verifica si la solicitud fue exitosa
        if not response.data:
            return jsonify({'error': f"Error en la consulta: {response}"}), 500
        
        # Devuelve los datos si no hay errores
        return jsonify(response.data), 200

    except Exception as e:
        # Maneja otros errores
        return jsonify({'error': f"Error interno del servidor: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=os.getenv('DEBUG', 'False') == 'True')
