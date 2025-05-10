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

    def send_command(self, command: str, data=None, timeout=5.0):
        """Versión robusta con manejo mejorado de protocolo"""
        try:
            # Verificar conexión activa
            if not self.connected or not self.socket:
                if not self.reconnect():
                    raise ConnectionError("No se pudo conectar al servidor")
            # Configurar timeout
            self.socket.settimeout(timeout)
            
            # 1. Enviar comando
            self.socket.sendall(command.encode() + b'\n')
            print(f"[NETWORK] Comando {command} enviado")

            # Manejo especial para comandos de autenticación
            if command in ["LOGIN", "REGISTER"]:
                # Esperar READY del servidor
                response = self.socket.recv(1024).decode().strip()
                print(f"[NETWORK] Respuesta inicial: {response}")

                if response == "NEED_LOGIN":
                    raise ConnectionError("Requiere autenticación primero")
                elif response != "READY":
                    # Manejar mensaje de bienvenida u otras respuestas
                    if response.startswith("WELCOME"):
                        # Volver a leer para obtener READY
                        response = self.socket.recv(1024).decode().strip()
                        if response != "READY":
                            raise ConnectionError(f"Protocolo inválido, esperaba READY, obtuve: {response}")
                    else:
                        raise ConnectionError(f"Respuesta inesperada: {response}")

                # 2. Enviar datos de autenticación
                payload = data.encode() if isinstance(data, str) else data
                print(f"[NETWORK] Enviando {len(payload)} bytes de datos...")
                self.socket.sendall(payload + b'\n')

                # 3. Recibir respuesta final
                final_response = self.socket.recv(1024).decode().strip()
                print(f"[NETWORK] Respuesta final: {final_response}")
                return final_response

            # Comandos especiales (no requieren READY)
            if command in ["LOGOUT", "EXIT"]:
                response = self.socket.recv(1024).decode().strip()
                print(f"[NETWORK] Respuesta {command}: {response}")
                return response

            # 2. Esperar READY para otros comandos
            response = self.socket.recv(1024).decode().strip()
            print(f"[NETWORK] Respuesta inicial: {response}")

            if response == "NEED_LOGIN":
                raise ConnectionError("Requiere autenticación primero")
            elif response != "READY":
                raise ConnectionError(f"Protocolo inválido, esperaba READY, obtuve: {response}")

            # 3. Enviar datos si existen
            if data:
                payload = data.encode() if isinstance(data, str) else data
                print(f"[NETWORK] Enviando {len(payload)} bytes de datos...")
                self.socket.sendall(payload + b'\n')

            # 4. Recibir respuesta final
            final_response = self.socket.recv(4096).decode().strip()
            print(f"[NETWORK] Respuesta final: {final_response}")
            return final_response

        except socket.timeout:
            print("[NETWORK] Timeout esperando respuesta")
            self.disconnect()
            raise ConnectionError("El servidor no respondió a tiempo")
        except Exception as e:
            print(f"[NETWORK] Error en comunicación: {str(e)}")
            self.disconnect()
            raise

    def _receive_response(self):
        """Helper para recibir respuestas"""
        try:
            response = self.socket.recv(1024).decode().strip()
            if not response:
                raise ConnectionError("Conexión cerrada por el servidor")
            return response
        except Exception as e:
            raise ConnectionError(f"Error recibiendo respuesta: {str(e)}")

    def _validate_connection(self):
        """Verifica si la conexión sigue activa"""
        try:
            # Envía un ping de prueba
            self.socket.settimeout(1.0)
            self.socket.sendall(b'PING\n')
            return self.socket.recv(16) == b'PONG\n'
        except:
            return False

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
        """Envía mensajes con manejo robusto de conexión y sesión"""
        max_retries = 2  # Reducimos a 2 intentos
        for attempt in range(max_retries):
            try:
                # Verificar conexión
                if not self.connected or not self._validate_connection():
                    if not self.reconnect():
                        raise ConnectionError("No se pudo conectar al servidor")
                
                # 1. Enviar comando SEND con \n final
                self.socket.sendall(b'SEND\n')
                print("[DEBUG] Comando SEND enviado")
                
                # 2. Esperar READY del servidor
                response = self._receive_response().strip()
                print(f"[DEBUG] Respuesta del servidor: {response}")
                
                if response == "NEED_LOGIN":
                    raise ConnectionError("Sesión expirada, requiere reautenticación")
                elif response != "READY":
                    raise ConnectionError(f"Protocolo inválido, esperaba READY, obtuve: {response}")
                
                # 3. Enviar destinatario y mensaje en formato estricto
                payload = f"{recipient}\n{message}\n".encode('utf-8')  # Aseguramos doble \n
                self.socket.sendall(payload)
                print(f"[DEBUG] Payload enviado: {payload.decode().strip()}")
                
                # 4. Recibir confirmación final
                final_response = self._receive_response().strip()
                print(f"[DEBUG] Respuesta final: {final_response}")
                
                return final_response == "MESSAGE_SENT"
                    
            except Exception as e:
                print(f"[ERROR] Intento {attempt+1} fallido: {str(e)}")
                if attempt == max_retries - 1:
                    return False
                time.sleep(0.5)
        return False

    def get_messages(self) -> list:
        try:
            # Configurar timeout largo para toda la operación
            self.socket.settimeout(30.0)
            
            # 1. Enviar comando GET
            self.socket.sendall(b"GET\n")
            
            # 2. Recibir cantidad de mensajes
            msg_count = int(self._receive_line())
            print(f"[CLIENT] Recibiendo {msg_count} mensajes")
            
            messages = []
            if msg_count > 0:
                # 3. Enviar confirmación READY
                self.socket.sendall(b"READY\n")
                
                # 4. Recibir cada mensaje con ACK
                for _ in range(msg_count):
                    msg_data = self._receive_line()
                    if not msg_data:
                        break
                    
                    # Enviar ACK inmediatamente
                    self.socket.sendall(b"ACK\n")
                    
                    # Parsear mensaje
                    parts = msg_data.split('|')
                    if len(parts) == 3:
                        messages.append({
                            'sender': parts[0],
                            'message': parts[1],
                            'time': parts[2]
                        })
            
            # 5. Confirmar finalización
            self.socket.sendall(b"GET_COMPLETE\n")
            return messages
            
        except socket.timeout:
            print("[CLIENT] Timeout en get_messages")
            return []
        except Exception as e:
            print(f"[CLIENT] Error en get_messages: {str(e)}")
            return []

    def _receive_line(self):
        """Helper para recibir líneas completas"""
        buffer = []
        while True:
            data = self.socket.recv(1)
            if not data or data == b'\n':
                return b''.join(buffer).decode()
            buffer.append(data)
    
    def reconnect(self):
        """Reconecta si la conexión está cerrada"""
        try:
            if not self.connected:
                print("[NETWORK] Intentando reconexión...")
                return self.connect()
            return True
        except Exception as e:
            print(f"[NETWORK] Error en reconexión: {str(e)}")
            return False

def encrypt_message(message: str) -> bytes:
    """Función dummy - Debes implementar o importar tu encriptación real"""
    return message.encode()

def decrypt_message(encrypted: bytes) -> str:
    """Función dummy - Debes implementar o importar tu desencriptación real"""
    return encrypted.decode()