import logging
from app.utils.db import get_mysql_connection, get_influxdb_client
from app.metrics import MYSQL_WRITE_SUCCESS, MYSQL_WRITE_FAILURE, INFLUX_WRITE_SUCCESS, INFLUX_WRITE_FAILURE
import os

def register_device(gateway_id, email):
    """
    Registra el dispositivo en la base de datos MySQL.
    Verifica si ya existe un dispositivo con el gateway_id en la tabla 'dispositivo'.
    Si no existe, busca el usuario por email en la tabla 'usuario' y, si se encuentra,
    inserta un nuevo registro en 'dispositivo'.
    
    Retorna un diccionario con la información:
      - status: 'registered' o 'exists' o 'user_not_found'
      - device_id: id autogenerado (si se registró)
      - message: mensaje informativo
    """
    try:
        connection = get_mysql_connection()
        cursor = connection.cursor()
        
        # Verificar si el dispositivo ya está registrado
        cursor.execute("SELECT id FROM dispositivo WHERE identificador = %s", (gateway_id,))
        dispositivo_existente = cursor.fetchone()
        
        if dispositivo_existente:
            return {
                "status": "exists",
                "device_id": dispositivo_existente[0],
                "message": "El dispositivo ya está registrado."
            }
        
        # Buscar usuario por email en la tabla 'usuario'
        cursor.execute("SELECT id FROM usuario WHERE email = %s", (email,))
        usuario = cursor.fetchone()
        
        if not usuario:
            return {
                "status": "user_not_found",
                "message": "No existe un usuario con el email proporcionado. Registre el usuario primero."
            }
        
        user_id = usuario[0]
        # Insertar el nuevo dispositivo
        cursor.execute(
            "INSERT INTO dispositivo (identificador, id_usuario) VALUES (%s, %s)",
            (gateway_id, user_id)
        )
        connection.commit()
        device_id = cursor.lastrowid
        
        logging.info("Dispositivo %s registrado para el usuario %s", gateway_id, user_id)
        return {
            "status": "registered",
            "device_id": device_id,
            "message": "Dispositivo registrado exitosamente."
        }
    except Exception as e:
        connection.rollback()
        logging.error("Error al registrar dispositivo %s: %s", gateway_id, str(e))
        return {
            "status": "error",
            "message": f"Error al registrar dispositivo: {str(e)}"
        }
    finally:
        cursor.close()
        connection.close()


def write_to_mysql(data):
    """
    Inserta la información en MySQL.
    Se espera que data sea un diccionario con la siguiente estructura:
    {
        "child_id": <id del dispositivo hijo>,
        "sensor_data": {
            "temp": <valor>,
            "hum": <valor>,
            "luz": <valor>,
            "hum_cap": <valor>,
            "hum_res": <valor>,
            "nivel_agua": <valor>
        },
        "gateway_id": <id del gateway>,
        "timestamp": <marca de tiempo>
    }
    """
    try:
        connection = get_mysql_connection()
        cursor = connection.cursor()
        sql = (
            "INSERT INTO device_data "
            "(id, temp, hum, nivel_agua, luz, hum_cap, hum_res)"
            "VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )
        cursor.execute(sql, (
            data["child_id"],
            data["sensor_data"]["temp"],
            data["sensor_data"]["hum"],
            data["sensor_data"]["nivel_agua"],
            data["sensor_data"]["luz"],
            data["sensor_data"]["hum_cap"],
            data["sensor_data"]["hum_res"]
        ))
        connection.commit()
        cursor.close()
        connection.close()
        MYSQL_WRITE_SUCCESS.inc()  
        logging.info("Escritura exitosa en MySQL para el dispositivo %s", data["child_id"])
        return True
    except Exception as e:
        MYSQL_WRITE_FAILURE.inc() 
        logging.error("Error al escribir en MySQL para el dispositivo %s: %s", data.get("child_id"), str(e))
        return False

def write_to_influxdb(data):
    """
    Inserta los datos del sensor en InfluxDB usando el cliente InfluxDB.
    Se espera que data tenga la estructura indicada en write_to_mysql.
    """
    try:
        influx_client = get_influxdb_client()
        write_api = influx_client.write_api()

        point = {
            "measurement": "sensor_data",
            "tags": {"device_id": data["child_id"]},
            "fields": {
                "temperature": data["sensor_data"]["temp"],
                "humidity": data["sensor_data"]["hum"],
                "level_water": data["sensor_data"]["nivel_agua"],
                "light": data["sensor_data"]["luz"],
                "soil_cap": data["sensor_data"]["hum_cap"],
                "soil_res": data["sensor_data"]["hum_res"]
            }
        }
        bucket = os.getenv("INFLUX_BUCKET", "sensor_bucket")
        write_api.write(bucket=bucket, record=point)
        influx_client.close()
        INFLUX_WRITE_SUCCESS.inc()  # Incrementa contador de éxito
        logging.info("Escritura exitosa en InfluxDB para el dispositivo %s", data["child_id"])
        return True
    except Exception as e:
        INFLUX_WRITE_FAILURE.inc()  # Incrementa contador de fallas
        logging.error("Error al escribir en InfluxDB para el dispositivo %s: %s", data.get("child_id"), str(e))
        return False

def process_device_data(data):
    """
    Ejecuta el dual write (MySQL e InfluxDB) y registra el estado de cada operación.
    Se espera que `data` tenga la estructura:
    {
        "child_id": "child123",
        "sensor_data": {
             "temp": ...,
             "hum": ...,
             "luz": ...,
             "hum_cap": ...,
             "hum_res": ...,
             "nivel_agua": ...
        },
        "gateway_id": "gatewayXYZ",    # Opcional para registro o auditoría
        "timestamp": 1234567890          # Opcional, marca de tiempo
    }
    Devuelve un diccionario con el estado de cada escritura.
    """
    status = {"mysql": False, "influxdb": False}

    status["mysql"] = write_to_mysql(data)
    status["influxdb"] = write_to_influxdb(data)

    if not status["mysql"]:
        logging.error("Falló la escritura en MySQL para el dispositivo %s", data.get("child_id"))
    if not status["influxdb"]:
        logging.error("Falló la escritura en InfluxDB para el dispositivo %s", data.get("child_id"))

    return status

