import socket
import logging
import configparser
from pathlib import Path
from typing import Optional, Union
import time

logger = logging.getLogger(__name__)

class NetworkClient:
    def __init__(self):
        """Inicializa el cliente de red cargando la configuración"""
        self.host: str = ""
        self.port: int = 0
        self.socket: Optional[socket.socket] = None
        self.connected: bool = False
        self._load_config()

    def _load_config(self):
        """Carga la configuración desde config.ini"""
        try:
            config = configparser.ConfigParser()
            config_path = Path(__file__).parent.parent / 'config' / 'config.ini'
            
            if not config_path.exists():
                raise FileNotFoundError(f"Archivo de configuración no encontrado: {config_path}")

            config.read(config_path)
            
            self.host = config['server']['host']
            self.port = int(config['server']['port'])
            
            logger.info(f"Configuración cargada - Servidor: {self.host}:{self.port}")

        except Exception as e:
            logger.error(f"Error al cargar configuración: {str(e)}")
            raise

    def connect(self, retries: int = 3, delay: float = 2.0) -> bool:
        """Versión mejorada del método de conexión"""
        for attempt in range(retries):
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(5.0)
                
                # Conexión básica
                self.socket.connect((self.host, self.port))
                
                # Handshake simplificado - Espera mensaje inicial del servidor
                welcome_msg = self.socket.recv(1024).decode().strip()
                if not welcome_msg:
                    raise ConnectionError("El servidor no envió mensaje de bienvenida")
                    
                logger.info(f"Mensaje de bienvenida del servidor: {welcome_msg}")
                self.connected = True
                return True
                
            except socket.timeout as e:
                logger.warning(f"Timeout en intento {attempt + 1}: {str(e)}")
            except ConnectionError as e:
                logger.warning(f"Error de protocolo (intento {attempt + 1}): {str(e)}")
            except Exception as e:
                logger.error(f"Error inesperado (intento {attempt + 1}): {str(e)}")
            
            time.sleep(delay)
        
        return False

    def send_command(self, command: str, data: Optional[Union[str, bytes]] = None) -> Optional[str]:
        try:
            # 1. Enviar comando
            self.socket.settimeout(10.0)
            self.socket.sendall(command.encode() + b'\n')
            print(f"[DEBUG] Comando enviado: {command}")

            if command == "LOGOUT":
                # Esperar respuesta con timeout extendido
                response = self.socket.recv(1024).decode().strip()
                print(f"[NETWORK] Respuesta LOGOUT: {response}")
                return response

            # 2. Esperar READY del servidor (con timeout)
            self.socket.settimeout(5.0)
            ready = self.socket.recv(1024).decode().strip()
            print(f"[DEBUG] Respuesta del servidor: {ready}")
            
            if ready != "READY":
                raise ConnectionError(f"Expected READY, got {ready}")

            # 3. Enviar datos (si existen)
            if data:
                print(f"[DEBUG] Enviando datos: {data[:20]}...")  # Muestra parte de los datos
                if isinstance(data, str):
                    self.socket.sendall(data.encode() + b'\n')
                else:
                    self.socket.sendall(data + b'\n')
            # 4. Esperar respuesta final
            response = self.socket.recv(4096).decode().strip()
            print(f"[DEBUG] Respuesta final: {response}")

            return response

        except socket.timeout:
            print("[ERROR] Timeout esperando respuesta del servidor")
            raise
        except Exception as e:
            print(f"[ERROR] Error en send_command: {str(e)}")
            raise

    def _receive_response(self) -> str:
        """Recibe datos del servidor con manejo de errores"""
        try:
            data = self.socket.recv(4096)
            if not data:
                raise ConnectionError("Conexión cerrada por el servidor")
            return data.decode().strip()
        except Exception as e:
            logger.error(f"Error al recibir datos: {str(e)}")
            raise

    def disconnect(self):
        """Cierra la conexión de forma segura"""
        if self.socket:
            try:
                if self.connected:
                    self.socket.sendall(b'EXIT')
                self.socket.close()
            except Exception as e:
                logger.error(f"Error al desconectar: {str(e)}")
            finally:
                self.socket = None
                self.connected = False
                logger.info("Desconectado del servidor")

    def send_message(self, recipient: str, message: str) -> bool:
        """Envía un mensaje cifrado al servidor"""
        try:
            encrypted = encrypt_message(message)
            response = self.send_command(
                "SEND",
                f"{recipient}\n".encode() + encrypted
            )
            return response == "MESSAGE_SENT"
        except Exception as e:
            logger.error(f"Error al enviar mensaje: {str(e)}")
            return False

    def get_messages(self) -> list:
        try:
            # Enviar comando GET
            self.socket.sendall(b"GET\n")
            print("[CLIENT] Comando GET enviado")
            
            # Recibir cantidad de mensajes
            msg_count = int(self.socket.recv(1024).decode().strip())
            print(f"[CLIENT] Mensajes por recibir: {msg_count}")
            
            messages = []
            if msg_count > 0:
                # Enviar READY para confirmar
                self.socket.sendall(b"READY\n")
                print("[CLIENT] Confirmación READY enviada")
                
                # Recibir cada mensaje
                for _ in range(msg_count):
                    msg_data = self.socket.recv(4096).decode().strip()
                    print(f"[CLIENT] Mensaje recibido: {msg_data[:50]}...")  # Muestra parte del mensaje
                    
                    # Enviar ACK por cada mensaje
                    self.socket.sendall(b"ACK\n")
                    
                    # Parsear mensaje
                    parts = msg_data.split('|')
                    if len(parts) == 3:
                        messages.append({
                            'sender': parts[0],
                            'message': parts[1],
                            'time': parts[2]
                        })
            
            return messages
            
        except Exception as e:
            print(f"[CLIENT] Error al obtener mensajes: {str(e)}")
            return []

def encrypt_message(message: str) -> bytes:
    """Función dummy - Debes implementar o importar tu encriptación real"""
    return message.encode()

def decrypt_message(encrypted: bytes) -> str:
    """Función dummy - Debes implementar o importar tu desencriptación real"""
    return encrypted.decode()