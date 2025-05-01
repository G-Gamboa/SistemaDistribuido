import hashlib
import os
from db import execute_query
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def hash_password(password):
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    return salt.hex(), key.hex()

def verify_password(stored_salt, stored_key, provided_password):
    try:
        salt = bytes.fromhex(stored_salt)
        stored_key_bytes = bytes.fromhex(stored_key)
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
    try:
        salt, key = hash_password(password)
        query = """
        INSERT INTO usuarios 
        (username, password_hash, salt, esta_activo) 
        VALUES (%s, %s, %s, TRUE)
        """
        result = execute_query(query, (username, key.hex(), salt.hex()))
        
        if result is None or result == 0:
            logger.error("Error: No se pudo registrar el usuario (consunta no ejecutada)")
            return False
        
        logger.info(f"Usuario {username} registrado exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"Error en registro: {str(e)}")
        return False

def verify_user(username, password):
    query = """
    SELECT password_hash, salt FROM usuarios 
    WHERE username = %s AND esta_activo = TRUE
    """
    user_data = execute_query(query, (username,), fetch=True)
    
    if not user_data or len(user_data) == 0:
        return False
        
    stored_key = user_data[0]['password_hash']
    stored_salt = user_data[0]['salt']
    return verify_password(stored_salt, stored_key, password)