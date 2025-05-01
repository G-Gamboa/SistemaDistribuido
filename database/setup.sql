-- Eliminación segura de tablas
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS logs;
DROP TABLE IF EXISTS mensajes;
DROP TABLE IF EXISTS usuarios;
SET FOREIGN_KEY_CHECKS = 1;

-- Creación de tablas
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(255) NOT NULL,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    esta_activo BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB;

CREATE TABLE mensajes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    remitente_id INT NOT NULL,
    destinatario_id INT NOT NULL,
    mensaje_cifrado TEXT NOT NULL,
    fecha_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (remitente_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (destinatario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX (destinatario_id)
) ENGINE=InnoDB;

CREATE TABLE logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    evento VARCHAR(50) NOT NULL,
    usuario_id INT NULL,
    ip_origen VARCHAR(45),
    detalles TEXT,
    fecha_evento DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL,
    INDEX (evento),
    INDEX (fecha_evento)
) ENGINE=InnoDB;

-- Usuario con todos los privilegios
CREATE USER IF NOT EXISTS 'mensajeria'@'localhost' IDENTIFIED BY 'contra123';
GRANT ALL PRIVILEGES ON AppMensajeria.* TO 'mensajeria'@'localhost';
GRANT RELOAD ON *.* TO 'mensajeria'@'localhost';
FLUSH PRIVILEGES;