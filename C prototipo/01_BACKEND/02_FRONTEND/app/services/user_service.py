# app/services/user_service.py

import logging
from app.utils.db import get_mysql_connection

def create_user(data):
    """
    Crea un nuevo usuario si no existe, basándose en el email.
    Se requieren: nombre, apellido y email.
    """
    nombre = data.get("nombre")
    apellido = data.get("apellido")
    email = data.get("email")
    
    if not (nombre and apellido and email):
        return {"status": "error", "message": "Datos incompletos."}
    
    try:
        connection = get_mysql_connection()
        cursor = connection.cursor()
        
        # Verificar existencia por email
        cursor.execute("SELECT id FROM usuario WHERE email = %s", (email,))
        usuario = cursor.fetchone()
        if usuario:
            return {"status": "exists", "user_id": usuario[0], "message": "El usuario ya existe."}
        
        # Crear nuevo usuario
        cursor.execute("INSERT INTO usuario (nombre, apellido, email) VALUES (%s, %s, %s)", (nombre, apellido, email))
        connection.commit()
        user_id = cursor.lastrowid
        return {"status": "created", "user_id": user_id, "message": "Usuario creado exitosamente."}
    except Exception as e:
        connection.rollback()
        logging.error("Error creando usuario: %s", str(e))
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        connection.close()

def delete_device(device_id, email):
    """
    Elimina un dispositivo si pertenece al usuario identificado por el email.
    Se verifica en la relación entre 'dispositivo' y 'usuario'.
    """
    try:
        connection = get_mysql_connection()
        cursor = connection.cursor()
        
        # Validar que el dispositivo pertenece al usuario
        query = """
        SELECT d.id FROM dispositivo d
        JOIN usuario u ON d.id_usuario = u.id
        WHERE d.id = %s AND u.email = %s
        """
        cursor.execute(query, (device_id, email))
        result = cursor.fetchone()
        if not result:
            return {"status": "not_found", "message": "Dispositivo no encontrado para el usuario proporcionado."}
        
        # Eliminar el dispositivo
        cursor.execute("DELETE FROM dispositivo WHERE id = %s", (device_id,))
        connection.commit()
        return {"status": "deleted", "device_id": device_id, "message": "Dispositivo eliminado exitosamente."}
    except Exception as e:
        connection.rollback()
        logging.error("Error eliminando dispositivo %s: %s", device_id, str(e))
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        connection.close()

def get_measurements_for_device(device_id):
    """
    Retorna las mediciones para un dispositivo específico.
    Se busca primero el 'identificador' del dispositivo y luego se consulta la tabla de mediciones.
    """
    try:
        connection = get_mysql_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Obtener el identificador (gateway) del dispositivo
        cursor.execute("SELECT identificador FROM dispositivo WHERE id = %s", (device_id,))
        device = cursor.fetchone()
        if not device:
            return {"status": "not_found", "message": "Dispositivo no encontrado."}
        
        identificador = device["identificador"]
        
        # Consultar la tabla de mediciones (asumiendo el nombre 'dispositivos_mediciones')
        cursor.execute("SELECT * FROM dispositivos_mediciones WHERE dispositivo_identificador = %s", (identificador,))
        measurements = cursor.fetchall()
        return {"status": "success", "device_id": device_id, "measurements": measurements}
    except Exception as e:
        logging.error("Error obteniendo mediciones para dispositivo %s: %s", device_id, str(e))
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        connection.close()

def get_measurements_for_user(email):
    """
    Retorna las mediciones para todos los dispositivos asociados a un usuario identificado por email.
    Se utiliza un join entre las tablas: dispositivos_mediciones, dispositivo y usuario.
    """
    try:
        connection = get_mysql_connection()
        cursor = connection.cursor(dictionary=True)
        
        query = """
        SELECT dm.* FROM dispositivos_mediciones dm
        JOIN dispositivo d ON dm.dispositivo_identificador = d.identificador
        JOIN usuario u ON d.id_usuario = u.id
        WHERE u.email = %s
        """
        cursor.execute(query, (email,))
        measurements = cursor.fetchall()
        return {"status": "success", "measurements": measurements}
    except Exception as e:
        logging.error("Error obteniendo mediciones para usuario %s: %s", email, str(e))
        return {"status": "error", "message": str(e)}
    finally:
        cursor.close()
        connection.close()
