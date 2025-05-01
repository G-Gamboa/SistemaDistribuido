import logging
from client.core.auth import AuthManager
from client.core.network import NetworkClient
from client.ui.cli import CLInterface
from client.config.config import load_config

def setup_logging():
    """Configura el sistema de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('client.log'),
            logging.StreamHandler()
        ]
    )

def main():
    # Configuración inicial
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Cargar configuración
        config = load_config()
        
        # Inicializar componentes
        network_client = NetworkClient(
            host=config['server']['host'],
            port=int(config['server']['port'])
        )
        
        auth_manager = AuthManager(network_client)
        cli = CLInterface(auth_manager, network_client)
        
        # Iniciar interfaz
        logger.info("Iniciando cliente...")
        cli.show_main_menu()
        
    except Exception as e:
        logger.error(f"Error fatal: {str(e)}")
    finally:
        if network_client.connected:
            network_client.disconnect()
        logger.info("Cliente terminado")

if __name__ == "__main__":
    main()