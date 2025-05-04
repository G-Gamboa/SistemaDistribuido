import hashlib
import os
from db import execute_query
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def hash_password(password):
    """Hash a password with a new salt"""
    salt = os.urandom(32)  # Genera un salt aleatorio
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    # Devuelve los valores en hexadecimal como strings
    return salt.hex(), key.hex()

def verify_password(stored_salt, stored_key, provided_password):
    """Verify a stored password against one provided by user"""
    try:
        # Convierte los hex strings de vuelta a bytes
        salt = bytes.fromhex(stored_salt)
        stored_key_bytes = bytes.fromhex(stored_key)
        
        # Genera el hash con la contraseña proporcionada
        new_key = hashlib.pbkdf2_hmac(
            'sha256',
            provided_password.encode('utf-8'),
            salt,
            100000
        )
        return stored_key_bytes == new_key
    except Exception as e:
        logger.error(f"Error en verificación de contraseña: {e}")
        return False

def register_user(username, password):
    """Register a new user with hashed password"""
    try:
        # Verificar si el usuario ya existe
        existing_user = execute_query(
            "SELECT id FROM usuarios WHERE username = %s",
            (username,),
            fetch=True
        )
        
        if existing_user:
            logger.warning(f"Intento de registrar usuario existente: {username}")
            return False
            
        # Obtener salt y hash (ya en formato hex)
        salt, key = hash_password(password)
        
        # Insertar en la base de datos (sin convertir a hex nuevamente)
        result = execute_query(
            "INSERT INTO usuarios (username, password_hash, salt) VALUES (%s, %s, %s)",
            (username, key, salt)  # Ya son strings hex, no necesitan .hex()
        )
        
        if not result:
            raise Exception("No se pudo insertar usuario")
            
        logger.info(f"Usuario {username} registrado exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"Error en registro: {str(e)}")
        return False

def verify_user(username, password):
    try:
        print(f"[DB] Verificando usuario: {username}")  # Debug
        query = "SELECT password_hash, salt FROM usuarios WHERE username = %s"
        result = execute_query(query, (username,), fetch=True)
        
        if not result:
            print(f"[DB] Usuario no encontrado: {username}")  # Debug
            return False
            
        print(f"[DB] Datos obtenidos de BD: {result}")  # Debug
        return verify_password(
            result[0]['salt'],
            result[0]['password_hash'],
            password
        )
    except Exception as e:
        print(f"[DB] Error en verificación: {str(e)}")  # Debug
        return False