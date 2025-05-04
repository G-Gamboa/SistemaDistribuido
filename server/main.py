import socket
import threading
from auth import verify_user, register_user
from message_handler import send_message, get_messages
from logger import log_event
import configparser
import sys
import os
from pathlib import Path

# Configuración robusta
def load_config():
    config = configparser.ConfigParser()
    config_file = Path(__file__).parent / "config" / "config.ini"
    
    if not config_file.exists():
        print(f"ERROR: No se encontró config.ini en {config_file}")
        sys.exit(1)
    
    config.read(config_file)
    
    required_sections = ['server', 'mysql', 'security']
    for section in required_sections:
        if not config.has_section(section):
            print(f"ERROR: Falta sección requerida [{section}] en config.ini")
            sys.exit(1)
    
    return config

config = load_config()

# Configuración del servidor
HOST = config['server']['host']
PORT = int(config['server']['port'])
MAX_CONNECTIONS = int(config['server']['max_connections'])

def handle_client(conn, addr):
    current_user = None
    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Desactiva Nagle
    log_event.info(f"Conexión establecida desde {addr}")

    try:
        # Paso 1: Enviar bienvenida y versión del protocolo
        conn.sendall(b"WELCOME AppMensajeria v1.0\n")

        # Paso 2: Bucle principal de comandos
        while True:
            try:
                # Configurar timeout para operaciones
                conn.settimeout(30.0)  # 30 segundos para recibir comandos

                # Recibir comando principal
                command = conn.recv(1024).decode().strip()
                if not command:
                    log_event.info(f"Conexión cerrada por {addr}")
                    break

                log_event.info(f"Comando recibido de {addr}: {command}")

                # Procesar comando REGISTER
                if command == "REGISTER":
                    conn.sendall(b"READY\n")  # Confirmar recepción de comando

                    # Recibir datos de registro
                    username = conn.recv(1024).decode().strip()
                    password = conn.recv(1024).decode().strip()
                    log_event.debug(f"Intento de registro: {username}")

                    # Procesar registro
                    if register_user(username, password):
                        conn.sendall(b"REGISTER_SUCCESS\n")
                        log_event.info(f"Registro exitoso: {username}")
                    else:
                        conn.sendall(b"REGISTER_FAILED\n")
                        log_event.warning(f"Fallo en registro: {username}")

                # Procesar comando LOGIN
                elif command == "LOGIN":
                    conn.sendall(b"READY\n")

                    # Recibir credenciales
                    username = conn.recv(1024).decode().strip()
                    password = conn.recv(1024).decode().strip()
                    log_event.debug(f"Intento de login: {username}")

                    # Validar credenciales
                    if verify_user(username, password):
                        current_user = username
                        conn.sendall(b"LOGIN_SUCCESS\n")
                        log_event.info(f"Login exitoso: {username}")
                    else:
                        conn.sendall(b"LOGIN_FAILED\n")
                        log_event.warning(f"Fallo en login: {username}")

                # Procesar comando SEND
                elif command == "SEND" and current_user:
                    conn.sendall(b"READY\n")

                    # Recibir datos del mensaje
                    recipient = conn.recv(1024).decode().strip()
                    encrypted_msg = conn.recv(4096)  # Mensaje cifrado

                    if send_message(current_user, recipient, encrypted_msg):
                        conn.sendall(b"MESSAGE_SENT\n")
                        log_event.info(f"Mensaje enviado de {current_user} a {recipient}")
                    else:
                        conn.sendall(b"MESSAGE_FAILED\n")
                        log_event.error(f"Error al enviar mensaje de {current_user}")

                # Procesar comando GET
                elif command == "GET" and current_user:
                    conn.sendall(b"READY\n")

                    messages = get_messages(current_user)
                    conn.sendall(str(len(messages)).encode() + b"\n")

                    # Esperar confirmación antes de enviar mensajes
                    if conn.recv(1024) == b"READY":
                        for msg in messages:
                            formatted = f"{msg['sender']}|{msg['message']}|{msg['time']}"
                            conn.sendall(formatted.encode())
                            conn.recv(1024)  # Esperar ACK por cada mensaje

                    log_event.info(f"Enviados {len(messages)} mensajes a {current_user}")

                # Comando EXIT
                elif command == "EXIT":
                    log_event.info(f"Usuario {current_user} cerró sesión")
                    conn.sendall(b"GOODBYE\n")
                    break

                # Comando no reconocido
                else:
                    conn.sendall(b"INVALID_COMMAND\n")
                    log_event.warning(f"Comando inválido de {addr}: {command}")

            except socket.timeout:
                log_event.error(f"Timeout con {addr}")
                conn.sendall(b"TIMEOUT\n")
                break
            except Exception as e:
                log_event.error(f"Error procesando comando: {str(e)}")
                conn.sendall(b"SERVER_ERROR\n")
                break

    except Exception as e:
        log_event.error(f"Error en la conexión con {addr}: {str(e)}")
    finally:
        if current_user:
            log_event.info(f"Desconectando usuario: {current_user}")
        conn.close()
        log_event.info(f"Conexión cerrada con {addr}")

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(MAX_CONNECTIONS)
        
        log_event("SERVER_START", details=f"Escuchando en {HOST}:{PORT}")
        print(f"Servidor escuchando en {HOST}:{PORT}")
        
        try:
            while True:
                conn, addr = s.accept()
                thread = threading.Thread(target=handle_client, args=(conn, addr))
                thread.daemon = True
                thread.start()
        except KeyboardInterrupt:
            log_event("SERVER_SHUTDOWN", details="Detenido por el usuario")
            print("\nDeteniendo servidor...")
            s.close()
            sys.exit(0)

if __name__ == "__main__":
    start_server()