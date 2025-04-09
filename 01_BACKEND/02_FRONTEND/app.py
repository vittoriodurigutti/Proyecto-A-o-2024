# app.py

import os
import logging
from flask import Flask, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.controllers.user_controller import user_blueprint

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

app.register_blueprint(user_blueprint)

# Endpoint para exponer métricas (si es necesario)
@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))  # Se puede configurar otro puerto
    app.run(host='0.0.0.0', port=port)
