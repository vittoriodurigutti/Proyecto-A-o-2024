from prometheus_client import Counter

MYSQL_WRITE_SUCCESS = Counter('mysql_write_success', 'Cantidad de escrituras exitosas en MySQL')
MYSQL_WRITE_FAILURE = Counter('mysql_write_failure', 'Cantidad de escrituras fallidas en MySQL')
INFLUX_WRITE_SUCCESS = Counter('influx_write_success', 'Cantidad de escrituras exitosas en InfluxDB')
INFLUX_WRITE_FAILURE = Counter('influx_write_failure', 'Cantidad de escrituras fallidas en InfluxDB')
