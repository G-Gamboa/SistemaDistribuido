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
        """Versión mejorada con manejo de protocolo robusto"""
        for attempt in range(1, 4):  # 3 intentos
            try:
                print(f"[AUTH] Intento {attempt} para {username}")
                
                # Enviar credenciales como un solo mensaje
                credentials = f"{username}\n{password}"
                response = self.network.send_command("LOGIN", credentials, timeout=10.0)
                
                if response == "LOGIN_SUCCESS":
                    self.current_user = username
                    print("[AUTH] Autenticación exitosa")
                    return True
                elif response == "LOGIN_FAILED":
                    print("[AUTH] Credenciales incorrectas")
                    return False
                elif response.startswith("LOGIN_FAILED:"):
                    print(f"[AUTH] Error de autenticación: {response.split(':', 1)[1]}")
                    return False
                else:
                    print(f"[AUTH] Respuesta inesperada: {response}")
                    continue
                    
            except ConnectionError as e:
                print(f"[AUTH] Error de conexión: {str(e)}")
                time.sleep(1)  # Espera antes de reintentar
                continue
            except Exception as e:
                print(f"[AUTH] Error inesperado: {str(e)}")
                self.network.disconnect()
                return False
        
        print("[AUTH] Todos los intentos fallaron")
        return False

    def logout(self) -> bool:
        try:
            print("[AUTH] Iniciando cierre de sesión")
            
            if not self.network.connected:
                print("[AUTH] No hay conexión activa")
                return False
                
            if not self.current_user:
                print("[AUTH] No hay sesión activa")
                return True
                
            response = self.network.send_command("LOGOUT", timeout=5.0)
            
            if response == "LOGOUT_SUCCESS":
                print("[AUTH] Sesión cerrada correctamente")
                self.current_user = None
                return True
            elif response == "LOGOUT_FAILED":
                print("[AUTH] Falló el cierre de sesión")
                return False
            else:
                print(f"[AUTH] Respuesta inesperada: {response}")
                return False
                
        except Exception as e:
            print(f"[AUTH] Error durante logout: {str(e)}")
            self.current_user = None
            return False