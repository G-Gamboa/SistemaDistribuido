from cryptography.fernet import Fernet
import base64
import os
from configparser import ConfigParser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar configuración
config = ConfigParser()
config.read('server/config.ini')

# Configuración de cifrado
KEY = config['security']['encryption_key'].encode()
cipher_suite = Fernet(base64.urlsafe_b64encode(KEY))

def encrypt_message(message):
    try:
        if isinstance(message, str):
            message = message.encode()
        return cipher_suite.encrypt(message)
    except Exception as e:
        logger.error(f"Error al cifrar mensaje: {e}")
        return None

def decrypt_message(encrypted_message):
    try:
        decrypted = cipher_suite.decrypt(encrypted_message)
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Error al descifrar mensaje: {e}")
        return None