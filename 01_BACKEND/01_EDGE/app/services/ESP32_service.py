import logging
from app.utils.db import get_mysql_connection, get_influxdb_client
from app.metrics import MYSQL_WRITE_SUCCESS, MYSQL_WRITE_FAILURE, INFLUX_WRITE_SUCCESS, INFLUX_WRITE_FAILURE
import os

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
            "(device_id, temperature, humidity, level_water, light, soil_cap, soil_res) "
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
