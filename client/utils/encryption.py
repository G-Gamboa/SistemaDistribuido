from cryptography.fernet import Fernet
import base64
import logging

# Configuración básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración directa (para desarrollo)
KEY = b'3iXvHvSAsUZBehzOSued-osDNnynApeLi9j-sAquPko=' 

try:
    # Validación de la clave
    cipher_suite = Fernet(KEY)
    logger.info("Módulo de encriptación configurado correctamente")
except Exception as e:
    logger.error(f"Error configurando encriptación: {str(e)}")
    raise

# Funciones que deben ser accesibles desde otros módulos
def encrypt_message(message: str) -> bytes:
    """
    Encripta un mensaje string.
    :param message: Mensaje a encriptar
    :return: Mensaje encriptado en bytes
    """
    if isinstance(message, str):
        message = message.encode('utf-8')
    return cipher_suite.encrypt(message)

def decrypt_message(encrypted_message: bytes) -> str:
    """
    Desencripta un mensaje.
    :param encrypted_message: Bytes del mensaje encriptado
    :return: String desencriptado
    """
    try:
        return cipher_suite.decrypt(encrypted_message).decode('utf-8')
    except Exception as e:
        logger.error(f"Error desencriptando mensaje: {str(e)}")
        raise

# Prueba automática al cargar el módulo
if __name__ == "__main__":
    test_msg = "Este es un mensaje de prueba"
    encrypted = encrypt_message(test_msg)
    decrypted = decrypt_message(encrypted)
    
    print(f"Prueba exitosa. Original: '{test_msg}' -> Desencriptado: '{decrypted}'")
    assert test_msg == decrypted, "¡Error en la prueba de encriptación/desencriptación!"