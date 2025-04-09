-- Creacion de la base de datos CGRH (Control y Gestion de Recusos Hidricos)
CREATE DATABASE IF NOT EXISTS cgrh_db_mysql;
USE cgrh_db_mysql;

-- Crear la tabla de usuarios
CREATE TABLE IF NOT EXISTS usuario (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    datos_contacto TEXT, -- campo opcional, de momento
    email VARCHAR(255) NOT NULL UNIQUE
);

-- Crear la tabla de dispositivos
CREATE TABLE IF NOT EXISTS dispositivo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    identificador VARCHAR(100) NOT NULL UNIQUE,  -- Puede ser la MAC o un valor único del micro
    -- configuraciones JSON,  -- Tentativo
    id_usuario INT NOT NULL,  -- Relaciona el dispositivo con un usuario existente
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_usuario 
        FOREIGN KEY (id_usuario) 
        REFERENCES usuario(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS dispositivos_mediciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dispositivo_identificador VARCHAR(100) NOT NULL,
    temp FLOAT NOT NULL,
    hum FLOAT NOT NULL,
    nivel_agua FLOAT NOT NULL,
    luz FLOAT NOT NULL,
    hum_cap FLOAT NOT NULL,
    hum_res FLOAT NOT NULL,
    fecha_medicion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_dispositivo_identificador 
        FOREIGN KEY (dispositivo_identificador)
        REFERENCES dispositivo(identificador)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
-----------------------------------------------------
-- Creación del usuario para operaciones en ambas tablas (data_admin)
-----------------------------------------------------
-- Creacion usuario para usuarios regulares (gestion datos personales, backend del front)
CREATE USER IF NOT EXISTS 'standar_user_mysql'@'%' IDENTIFIED BY 'standar_user';
GRANT SELECT, INSERT, UPDATE ON cgrh_db_mysql.usuario TO 'standar_user_mysql'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON cgrh_db_mysql.dispositivo TO 'standar_user_mysql'@'%';

-----------------------------------------------------
-- Creación del usuario para el registro de dispositivos
-----------------------------------------------------
CREATE USER IF NOT EXISTS 'device_reg_mysql'@'%' IDENTIFIED BY 'device_reg';
GRANT INSERT ON cgrh_db_mysql.dispositivo TO 'device_reg_mysql'@'%';

-----------------------------------------------------
-- Usuario Administrador (para no utilizar el root)
-----------------------------------------------------
CREATE USER IF NOT EXISTS 'db_admin_mysql'@'%' IDENTIFIED BY 'db_admin';
GRANT ALL PRIVILEGES ON cgrh_db_mysql.* TO 'db_admin_mysql'@'%';

-----------------------------------------------------
-- Implementacion de los permisos.
FLUSH PRIVILEGES;