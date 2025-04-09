# config/config.py

import os

class Config:
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = os.getenv('MYSQL_PORT', 3306)
    MYSQL_USER = os.getenv('MYSQL_USER', 'tu_usuario')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'tu_contraseña')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'cgrh_db_mysql')
