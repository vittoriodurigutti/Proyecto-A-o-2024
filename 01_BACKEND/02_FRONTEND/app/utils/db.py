import os
import mysql.connector
from influxdb_client import InfluxDBClient

def get_mysql_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "password"),
        database=os.getenv("DB_DATABASE", "devices_db")
    )

def get_influxdb_client():
    url = os.getenv("INFLUX_URL", "http://localhost:8086")
    token = os.getenv("INFLUX_TOKEN", "my-token")
    org = os.getenv("INFLUX_ORG", "my-org")
    return InfluxDBClient(url=url, token=token, org=org)