import os
import logging
from pathlib import Path

# Configurar directorio de logs
LOG_DIR = Path(__file__).parent / "logs"
LOG_FILE = LOG_DIR / "server.log"

# Crear directorio si no existe
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'  # Append mode
)

def log_event(event_type, username=None, details=""):
    try:
        log_msg = f"{event_type} - User: {username or 'SYSTEM'} - Details: {details}"
        logging.info(log_msg)
    except Exception as e:
        print(f"FALLBACK LOG ERROR: {str(e)}")  # Fallback mínimo