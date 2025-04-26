import socket
import threading
from auth import verify_user, register_user
from message_handler import send_message, get_messages
from logger import log_event
import configparser
import sys

# Configuración
config = configparser.ConfigParser()
config.read('server/config.ini')

HOST = config['server']['host']
PORT = int(config['server']['port'])
MAX_CONNECTIONS = int(config['server']['max_connections'])

def handle_client(conn, addr):
    current_user = None
    try:
        log_event("CONNECTION_ATTEMPT", details=f"IP: {addr[0]}")
        
        # Fase de autenticación/registro
        action = conn.recv(1024).decode().strip()
        
        if action == "REGISTER":
            username = conn.recv(1024).decode().strip()
            password = conn.recv(1024).decode().strip()
            
            if register_user(username, password):
                conn.sendall(b'REGISTER_SUCCESS')
                log_event("REGISTER_SUCCESS", username)
            else:
                conn.sendall(b'REGISTER_FAILED')
                log_event("REGISTER_FAILED", details=username)
            return
            
        elif action == "LOGIN":
            username = conn.recv(1024).decode().strip()
            password = conn.recv(1024).decode().strip()
            
            if verify_user(username, password):
                conn.sendall(b'LOGIN_SUCCESS')
                current_user = username
                log_event("LOGIN_SUCCESS", username)
            else:
                conn.sendall(b'LOGIN_FAILED')
                log_event("LOGIN_FAILED", details=username)
                return
        else:
            conn.sendall(b'INVALID_ACTION')
            return
            
        # Bucle principal de mensajes
        while True:
            command = conn.recv(1024).decode().strip()
            
            if command == "SEND":
                recipient = conn.recv(1024).decode().strip()
                encrypted_msg = conn.recv(4096)  # Mensaje cifrado
                
                if send_message(current_user, recipient, encrypted_msg):
                    conn.sendall(b'MESSAGE_SENT')
                else:
                    conn.sendall(b'MESSAGE_FAILED')
                    
            elif command == "GET":
                messages = get_messages(current_user)
                conn.sendall(str(len(messages)).encode())
                
                if conn.recv(1024) == b'READY':
                    for msg in messages:
                        formatted = f"{msg['sender']}|{msg['message']}|{msg['time']}"
                        conn.sendall(formatted.encode())
                        conn.recv(1024)  # Esperar ACK
                        
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