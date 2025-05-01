import configparser
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_config():
    """Carga la configuración desde config.ini"""
    config = configparser.ConfigParser()
    config_file = Path(__file__).parent.parent / 'config/config.ini'
    
    try:
        if not config_file.exists():
            raise FileNotFoundError(f"Archivo de configuración no encontrado: {config_file}")
            
        config.read(config_file)
        
        # Validar secciones requeridas
        required_sections = ['server', 'client']
        for section in required_sections:
            if not config.has_section(section):
                raise ValueError(f"Falta sección requerida: [{section}]")
                
        return config
        
    except Exception as e:
        logger.error(f"Error al cargar configuración: {str(e)}")
        raise