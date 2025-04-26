from db import execute_query
from encryption import encrypt_message, decrypt_message
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_message(sender, receiver, message):
    try:
        # Obtener IDs de usuarios
        sender_id = get_user_id(sender)
        receiver_id = get_user_id(receiver)
        
        if not sender_id or not receiver_id:
            return False
            
        # Cifrar mensaje
        encrypted_msg = encrypt_message(message)
        if not encrypted_msg:
            return False
            
        # Insertar mensaje
        query = """
        INSERT INTO mensajes 
        (remitente_id, destinatario_id, mensaje_cifrado) 
        VALUES (%s, %s, %s)
        """
        result = execute_query(query, (sender_id, receiver_id, encrypted_msg))
        return result is not None and result > 0
        
    except Exception as e:
        logger.error(f"Error enviando mensaje: {e}")
        return False

def get_messages(username):
    try:
        user_id = get_user_id(username)
        if not user_id:
            return []
            
        query = """
        SELECT u.username as sender, m.mensaje_cifrado, m.fecha_envio 
        FROM mensajes m 
        JOIN usuarios u ON m.remitente_id = u.id 
        WHERE m.destinatario_id = %s 
        ORDER BY m.fecha_envio DESC
        """
        messages = execute_query(query, (user_id,), fetch=True)
        
        if not messages:
            return []
            
        decrypted_messages = []
        for msg in messages:
            decrypted = decrypt_message(msg['mensaje_cifrado'])
            if decrypted:
                decrypted_messages.append({
                    'sender': msg['sender'],
                    'message': decrypted,
                    'time': msg['fecha_envio']
                })
        return decrypted_messages
        
    except Exception as e:
        logger.error(f"Error obteniendo mensajes: {e}")
        return []

def get_user_id(username):
    query = "SELECT id FROM usuarios WHERE username = %s"
    result = execute_query(query, (username,), fetch=True)
    return result[0]['id'] if result else None