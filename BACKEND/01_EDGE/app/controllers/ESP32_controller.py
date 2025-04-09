from flask import Blueprint, request, jsonify
from app.services.ESP32_service import process_device_data

esp32_blueprint = Blueprint('esp32', __name__)

@esp32_blueprint.route('/api/esp32/data', methods=['POST'])
def register_device_data():
    try:
        # Intentamos obtener los datos del body ya sea como form data o JSON.
        data = request.form.to_dict() or request.get_json()
        if not data:
            return jsonify({"message": "No se proporcionaron datos"}), 400

        # Se espera que data contenga las claves:
        # "id", "temp", "hum", "nivel_agua", "luz", "hum_cap", "hum_res"
        result = process_device_data(data)

        return jsonify({
            "message": "Datos procesados",
            "status": result
        }), 200
    except Exception as e:
        return jsonify({
            "message": "Error al procesar los datos",
            "error": str(e)
        }), 500
