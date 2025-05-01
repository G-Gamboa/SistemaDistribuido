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
        # 1. Siempre registrar en archivo log
        logging.info(f"{event_type}|{username or 'system'}|{details}")
        
        # 2. Intentar registrar en MySQL
        try:
            user_id = None
            if username:
                user_data = execute_query(
                    "SELECT id FROM usuarios WHERE username = %s", 
                    (username,),
                    fetch=True
                )
                user_id = user_data[0]['id'] if user_data else None
            
            execute_query(
                """INSERT INTO logs 
                (evento, usuario_id, detalles) 
                VALUES (%s, %s, %s)""",
                (event_type, user_id, str(details)[:500])
              )  # Limitar longitud
        except Exception as db_error:
            logging.error(f"Error en BD al registrar log: {str(db_error)[:200]}")
            
    except Exception as e:
        print(f"ERROR CRÍTICO EN SISTEMA DE LOGS: {str(e)}")