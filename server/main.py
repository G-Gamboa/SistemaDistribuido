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
    try:
        log_event("CONNECTION_ATTEMPT", details=f"IP: {addr[0]}")
        conn.sendall(b"WELCOME AppMensajeria v1.0\n")
        
        action = conn.recv(1024).decode().strip()
        print(f"Acción recibida: {action}")

        if action == "REGISTER":
            username = conn.recv(1024).decode().strip()
            password = conn.recv(1024).decode().strip()
            
            if register_user(username, password):
                conn.sendall(b'REGISTER_SUCCESS\n')
                log_event("REGISTER_SUCCESS", username)
            else:
                conn.sendall(b'REGISTER_FAILED: Usuario ya existe o error en BD\n')
                log_event("REGISTER_FAILED", details=username)
            return
            
        elif action == "LOGIN":
            try:
                print("[SERVER] Enviando READY para credenciales")
                conn.sendall(b"READY\n")  # Confirmación para recibir credenciales
                
                # Recibir ambas credenciales juntas
                credentials = conn.recv(1024).decode().strip()
                print(f"[SERVER] Credenciales recibidas (raw): {credentials}")
                
                # Separar usuario y contraseña
                parts = credentials.split('\n')
                if len(parts) != 2:
                    raise ValueError("Formato de credenciales incorrecto")
                    
                username, password = parts[0], parts[1]
                print(f"[SERVER] Procesando login para: {username}")
                
                if verify_user(username, password):
                    conn.sendall(b"LOGIN_SUCCESS\n")
                    current_user = username
                    print(f"[SERVER] Login exitoso: {username}")
                else:
                    conn.sendall(b"LOGIN_FAILED\n")
                    print(f"[SERVER] Login fallido: {username}")
                    
            except Exception as e:
                print(f"[SERVER] Error en login: {str(e)}")
                conn.sendall(b"LOGIN_ERROR\n")
        else:
            conn.sendall(b'INVALID_ACTION')
            return
            
        while True:
            command = conn.recv(1024).decode().strip()
            
            if command == "SEND":
                recipient = conn.recv(1024).decode().strip()
                encrypted_msg = conn.recv(4096)
                
                if send_message(current_user, recipient, encrypted_msg):
                    conn.sendall(b'MESSAGE_SENT\n')
                else:
                    conn.sendall(b'MESSAGE_FAILED\n')
                    
            elif command == "GET":
                try:
                    messages = get_messages(current_user)
                    print(f"[DEBUG] Mensajes encontrados: {len(messages)}")  # Log de depuración
                    
                    # Enviar cantidad de mensajes
                    conn.sendall(str(len(messages)).encode() + b"\n")
                    
                    # Esperar confirmación READY con timeout
                    ready = conn.recv(1024).decode().strip()
                    if ready != "READY":
                        raise ConnectionError(f"Se esperaba READY, se recibió: {ready}")
                    
                    # Enviar cada mensaje con confirmación
                    for msg in messages:
                        formatted = f"{msg['sender']}|{msg['message']}|{msg['time']}"
                        conn.sendall(formatted.encode() + b"\n")
                        
                        # Esperar ACK por cada mensaje
                        ack = conn.recv(3).decode().strip()
                        if ack != "ACK":
                            raise ConnectionError("Falta confirmación ACK")
                            
                    print(f"[DEBUG] Todos los mensajes enviados a {current_user}")
                    
                except Exception as e:
                    print(f"[ERROR] Error al enviar mensajes: {str(e)}")
                    conn.sendall(b"ERROR\n")    

                    
            elif command == "EXIT":
                log_event("LOGOUT", current_user)
                break
                
    except Exception as e:
        log_event("CONNECTION_ERROR", current_user, str(e))
    finally:
        conn.close()

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