from flask import Blueprint, request, jsonify
from app.services.ESP32_service import process_device_data, register_device

esp32_blueprint = Blueprint('esp32', __name__)

# Ruta para procesar datos de mediciones
@esp32_blueprint.route('/api/esp32/data', methods=['POST'])
def register_device_data():
    try:
        data = request.form.to_dict() or request.get_json()
        if not data:
            return jsonify({"message": "No se proporcionaron datos"}), 400

        # Se espera que data contenga las claves para el registro de mediciones
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

# Ruta para registro condicional del dispositivo
@esp32_blueprint.route('/api/esp32/register', methods=['POST'])
def register_device_route():
    try:
        data = request.get_json()
        gateway_id = data.get("gateway_id")
        email = data.get("email")
        
        if not gateway_id or not email:
            return jsonify({"message": "Se requieren gateway_id y email"}), 400
        
        result = register_device(gateway_id, email)
        # Si se creó el dispositivo de forma exitosa se retorna un código 201, de lo contrario un mensaje adecuado.
        if result.get("status") == "registered":
            return jsonify(result), 201
        else:
            return jsonify(result), 200
    except Exception as e:
        return jsonify({
            "message": "Error al registrar el dispositivo",
            "error": str(e)
        }), 500
