import logging
import socket
import time
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
        try:
            print(f"[AUTH] Preparando credenciales para {username}")
            
            # Envía usuario y contraseña como un solo mensaje separado por \n
            credentials = f"{username}\n{password}"
            response = self.network.send_command("LOGIN", credentials)
            
            print(f"[AUTH] Respuesta del servidor: {response}")
            
            if response == "LOGIN_SUCCESS":
                print("[AUTH] Autenticación exitosa")
                return True
            elif response == "LOGIN_FAILED":
                print("[AUTH] Credenciales incorrectas")
                return False
            else:
                print("[AUTH] Respuesta inesperada del servidor")
                return False
                
        except Exception as e:
            print(f"[AUTH] Error durante login: {str(e)}")
            return False

    def logout(self):
        try:
            print("[AUTH] Iniciando cierre de sesión")
            
            if not self.network.connected:
                print("[AUTH] No hay conexión activa")
                return False
                
            # Enviar comando LOGOUT con timeout extendido
            response = self.network.send_command("LOGOUT", timeout=10.0)
            
            if response == "LOGOUT_SUCCESS":
                print("[AUTH] Sesión cerrada correctamente")
                self.current_user = None
                return True
            else:
                print(f"[AUTH] Respuesta inesperada: {response}")
                return False
                
        except socket.timeout:
            print("[AUTH] El servidor no respondió a tiempo")
            return False
        except Exception as e:
            print(f"[AUTH] Error durante logout: {str(e)}")
            return False