from db import execute_query
import socket
import logging
from datetime import datetime

logging.basicConfig(
    filename='server/logs/server.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_event(event_type, username=None, details=""):
    try:
        user_id = None
        if username:
            user_id = execute_query(
                "SELECT id FROM usuarios WHERE username = %s",
                (username,),
                fetch=True
            )
            user_id = user_id[0]['id'] if user_id else None
            
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        
        query = """
        INSERT INTO logs 
        (evento, usuario_id, ip_origen, detalles) 
        VALUES (%s, %s, %s, %s)
        """
        execute_query(query, (event_type, user_id, ip_address, details))
        
        # También registrar en archivo log
        log_message = f"{event_type} - User: {username or 'SYSTEM'} - Details: {details}"
        logging.info(log_message)
        
    except Exception as e:
        logging.error(f"Error registrando evento: {e}")