from cryptography.fernet import Fernet
import base64
import os
from configparser import ConfigParser
import logging
from pathlib import Path

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config():
    try:
        config = ConfigParser()
        config_file = Path(__file__).parent / 'config.ini'
        
        if not config_file.exists():
            logger.error(f"Archivo de configuración no encontrado en: {config_file}")
            raise FileNotFoundError(f"Config file not found at {config_file}")
        
        config.read(config_file)
        
        if not config.has_section('security'):
            logger.error("La sección [security] no existe en config.ini")
            raise KeyError("Missing [security] section in config")
            
        return config
    except Exception as e:
        logger.error(f"Error cargando configuración: {e}")
        raise

try:
    config = load_config()
    KEY = config['security']['encryption_key'].strip().encode()
    
    # Validar la clave
    if len(base64.urlsafe_b64decode(KEY)) != 32:
        raise ValueError("La clave de encriptación debe tener 32 bytes en base64")
        
    cipher_suite = Fernet(base64.urlsafe_b64encode(KEY))
    logger.info("Configuración de encriptación cargada correctamente")
    
except Exception as e:
    logger.error(f"Error fatal en configuración de encriptación: {e}")
    raise