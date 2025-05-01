import sys
import os
from pathlib import Path
import logging

sys.path.append(str(Path(__file__).parent.parent))
from client.core.auth import AuthManager
from client.core.network import NetworkClient
from client.ui.cli import CLInterface
from client.config.config import load_config

def setup_logging():
    """Configura el sistema de logging"""
    log_file = Path(__file__).parent / 'client.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ],
        encoding='utf-8'  # Solo para Python 3.9+
    )

def main():
    # Configuración inicial
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Iniciando cliente...")
        
        # Inicializa NetworkClient sin parámetros (ya carga config.ini internamente)
        network_client = NetworkClient()
        
        # Intenta conectar automáticamente
        if not network_client.connect():
            logger.error("No se pudo conectar al servidor")
            return
            
        auth_manager = AuthManager(network_client)
        cli = CLInterface(auth_manager, network_client)
        
        # Inicia la interfaz
        cli.show_main_menu()
        
    except Exception as e:
        logger.error(f"Error fatal: {str(e)}", exc_info=True)
    finally:
        if 'network_client' in locals() and network_client.connected:
            network_client.disconnect()
        logger.info("Cliente terminado")

if __name__ == "__main__":
    main()