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
            username = conn.recv(1024).decode().strip()
            password = conn.recv(1024).decode().strip()
            
            if verify_user(username, password):
                conn.sendall(b'LOGIN_SUCCESS\n')
                current_user = username
                log_event("LOGIN_SUCCESS", username)
            else:
                conn.sendall(b'LOGIN_FAILED\n')
                log_event("LOGIN_FAILED", details=username)
                return
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
                messages = get_messages(current_user)
                conn.sendall(str(len(messages)).encode() + b"\n")  # Envía cantidad
                
                # Espera confirmación READY con timeout
                try:
                    ready_signal = conn.recv(1024).decode().strip()
                    if ready_signal == "READY":
                        for msg in messages:
                            formatted = f"{msg['sender']}|{msg['message']}|{msg['time']}\n"
                            conn.sendall(formatted.encode())
                            # Espera ACK por cada mensaje
                            ack = conn.recv(2)
                            if ack != b"OK":
                                break
                    else:
                        log_event(f"Señal inválida esperando mensajes: {ready_signal}", details="Se esperaba 'READY'")
                except socket.timeout:
                    log_event("Timeout esperando READY para enviar mensajes", details="Tiempo de espera agotado")
                                    
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