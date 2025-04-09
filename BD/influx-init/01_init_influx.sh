#!/bin/bash
# Espera 60 segundos para que InfluxDB se inicie completamente
sleep 60

ORG="ISPC"
BUCKET_NAME="cgrh_db_influx"

echo "Creando token para registro de dispositivos..."
if [ -z "$BUCKET_ID" ]; then
  echo "BUCKET_ID no está definido; creando token con --all-access."
  influx auth create \
    --org "$ORG" \
    --description "Token for device registration (device_reg_influx)" \
    --all-access
else
  influx auth create \
    --org "$ORG" \
    --read-bucket "$BUCKET_ID" \
    --write-bucket "$BUCKET_ID" \
    --description "Token for device registration (device_reg_influx)"
fi

echo "Creando token para Grafana (solo lectura)..."
if [ -z "$BUCKET_ID" ]; then
  echo "BUCKET_ID no está definido; creando token con --all-access (Nota: Esto dará acceso completo)."
  influx auth create \
    --org "$ORG" \
    --description "Token for Grafana read access (device_reg_grafana)" \
    --all-access
else
  influx auth create \
    --org "$ORG" \
    --read-bucket "$BUCKET_ID" \
    --description "Token for Grafana read access (device_reg_grafana)"
fi

echo "Creando token para estándar (solo lectura)..."
if [ -z "$BUCKET_ID" ]; then
  echo "BUCKET_ID no está definido; creando token con --all-access (Nota: Esto dará acceso completo)."
  influx auth create \
    --org "$ORG" \
    --description "Token for standard user access (standar_user_influx)" \
    --all-access
else
  influx auth create \
    --org "$ORG" \
    --read-bucket "$BUCKET_ID" \
    --description "Token for standard user access (standar_user_influx)"
fi

echo "Lista de tokens creados:"
influx auth list

echo "Finalizado la creación de tokens en InfluxDB."
