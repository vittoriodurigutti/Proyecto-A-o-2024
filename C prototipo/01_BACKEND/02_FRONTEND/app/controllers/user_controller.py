# app/controllers/user_controller.py

from flask import Blueprint, request, jsonify
from app.services.user_service import (
    create_user,
    delete_device,
    get_measurements_for_device,
    get_measurements_for_user
)

user_blueprint = Blueprint('user', __name__)

# Endpoint para crear usuario (no se permite eliminar usuario)
@user_blueprint.route('/api/users', methods=['POST'])
def create_user_route():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No se proporcionaron datos"}), 400
    result = create_user(data)
    status_code = 201 if result.get("status") == "created" else 200
    return jsonify(result), status_code

# Endpoint para eliminar dispositivo (se requiere confirmar con email)
@user_blueprint.route('/api/devices', methods=['DELETE'])
def delete_device_route():
    data = request.get_json()
    device_id = data.get("device_id")
    email = data.get("email")
    if not device_id or not email:
        return jsonify({"message": "Se requiere device_id y email"}), 400
    result = delete_device(device_id, email)
    return jsonify(result), 200

# Endpoint para obtener mediciones de un dispositivo específico (por id)
@user_blueprint.route('/api/measurements/<int:device_id>', methods=['GET'])
def get_device_measurements_route(device_id):
    result = get_measurements_for_device(device_id)
    if result.get("status") != "success":
        return jsonify(result), 404
    return jsonify(result), 200

# Endpoint para obtener mediciones de todos los dispositivos de un usuario (por email)
@user_blueprint.route('/api/measurements', methods=['GET'])
def get_user_measurements_route():
    email = request.args.get("email")
    if not email:
        return jsonify({"message": "Se requiere el email como parámetro de consulta"}), 400
    result = get_measurements_for_user(email)
    if result.get("status") != "success":
        return jsonify(result), 404
    return jsonify(result), 200
