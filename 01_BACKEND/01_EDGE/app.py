# app.py
import os
import logging
from flask import Flask, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.controllers.ESP32_controller import esp32_blueprint

# Configurar logging para depuración
logging.basicConfig(level=logging.INFO)

# Instanciar la aplicación Flask
app = Flask(__name__)

app.register_blueprint(esp32_blueprint)

# Endpoint para exponer las métricas para Prometheus
@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
