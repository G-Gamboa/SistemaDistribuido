import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class AuthManager:
    def __init__(self, network_client):
        self.network = network_client
        self.current_user: Optional[str] = None

    def register(self, username: str, password: str) -> bool:
        """Registra un nuevo usuario en el servidor"""
        try:
            if not username or not password:
                logger.error("Nombre de usuario o contraseña vacíos")
                return False

            response = self.network.send_command(
                "REGISTER",
                f"{username}\n{password}"
            )
            
            if response == "REGISTER_SUCCESS":
                logger.info(f"Usuario {username} registrado exitosamente")
                return True
            else:
                logger.error(f"Error en registro: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error en registro: {str(e)}")
            return False

    def login(self, username: str, password: str) -> bool:
        """Autentica un usuario con el servidor"""
        try:
            response = self.network.send_command(
                "LOGIN", 
                f"{username}\n{password}"
            )
            
            if response == "LOGIN_SUCCESS":
                self.current_user = username
                logger.info(f"Usuario {username} autenticado")
                return True
            else:
                logger.error(f"Error en autenticación: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error en login: {str(e)}")
            return False

    def logout(self) -> bool:
        """Cierra la sesión del usuario"""
        try:
            if self.current_user:
                response = self.network.send_command("LOGOUT")
                if response == "LOGOUT_SUCCESS":
                    logger.info(f"Usuario {self.current_user} cerró sesión")
                    self.current_user = None
                    return True
            return False
        except Exception as e:
            logger.error(f"Error al cerrar sesión: {str(e)}")
            return False