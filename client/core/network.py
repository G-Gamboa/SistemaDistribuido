import socket
import logging
from typing import Optional, Union
from client.utils.encryption import encrypt_message, decrypt_message

logger = logging.getLogger(__name__)

class NetworkClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.connected = False

    def connect(self) -> bool:
        """Establece conexión con el servidor"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.port))
            self.connected = True
            logger.info("Conexión establecida con el servidor")
            return True
        except Exception as e:
            logger.error(f"Error al conectar: {str(e)}")
            self.connected = False
            return False

    def disconnect(self):
        """Cierra la conexión con el servidor"""
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                logger.error(f"Error al desconectar: {str(e)}")
            finally:
                self.socket = None
                self.connected = False

    def send_command(self, command: str, data: Optional[Union[str, bytes]] = None) -> Optional[str]:
        """Envía un comando al servidor y recibe respuesta"""
        if not self.connected:
            logger.error("No hay conexión con el servidor")
            return None

        try:
            # Enviar comando
            self.socket.sendall(command.encode() + b'\n')
            
            # Esperar confirmación
            response = self._receive_response()
            if response != "READY":
                raise ConnectionError("Servidor no está listo")
                
            # Enviar datos si existen
            if data:
                if isinstance(data, str):
                    self.socket.sendall(data.encode() + b'\n')
                else:
                    self.socket.sendall(data + b'\n')
                
            # Recibir respuesta final
            return self._receive_response()
            
        except Exception as e:
            logger.error(f"Error en comunicación: {str(e)}")
            self.disconnect()
            return None

    def _receive_response(self) -> str:
        """Recibe datos del servidor"""
        try:
            data = self.socket.recv(4096)
            if not data:
                raise ConnectionError("Conexión cerrada por el servidor")
            return data.decode().strip()
        except Exception as e:
            logger.error(f"Error al recibir datos: {str(e)}")
            raise

    def send_message(self, recipient: str, message: str) -> bool:
        """Envía un mensaje cifrado al servidor"""
        encrypted = encrypt_message(message)
        response = self.send_command(
            "SEND",
            f"{recipient}\n".encode() + encrypted
        )
        return response == "MESSAGE_SENT"

    def get_messages(self) -> list:
        """Obtiene mensajes nuevos del servidor"""
        response = self.send_command("GET_MESSAGES")
        if not response or not response.isdigit():
            return []
            
        count = int(response)
        messages = []
        
        for _ in range(count):
            msg_data = self._receive_response()
            if msg_data:
                parts = msg_data.split('|', 2)
                if len(parts) == 3:
                    sender, encrypted_msg, timestamp = parts
                    try:
                        decrypted = decrypt_message(encrypted_msg.encode())
                        messages.append({
                            'sender': sender,
                            'message': decrypted,
                            'time': timestamp
                        })
                    except Exception as e:
                        logger.error(f"Error al desencriptar mensaje: {str(e)}")
        
        return messages