from cryptography.fernet import Fernet
import base64
import logging

# Configura logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Clave CORRECTA (la misma de tu config.ini)
KEY_STR = '3iXvHvSAsUZBehzOSued-osDNnynApeLi9j-sAquPko='

try:
    # Paso 1: Verificar formato
    if len(KEY_STR) != 44 or not KEY_STR.endswith('='):
        raise ValueError("Formato de clave inválido")
    
    # Paso 2: Codificar a bytes
    KEY = KEY_STR.encode('ascii')
    
    # Paso 3: Validar con Fernet
    Fernet(KEY)  # Esto lanzará error si la clave es inválida
    
    # Configuración exitosa
    cipher_suite = Fernet(KEY)
    logger.info("Encriptación configurada correctamente")
    
except Exception as e:
    logger.error(f"Error fatal: {e}")
    print(f"ERROR: {type(e).__name__}: {e}")
    print(f"Clave usada: {KEY_STR}")
    print(f"Longitud: {len(KEY_STR)} caracteres")
    raise