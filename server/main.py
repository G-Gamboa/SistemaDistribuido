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
        
        while True:
            command = conn.recv(1024).decode().strip()
            print(f"[SERVER] Comando recibido: {command}")

            if not command:
                break
                
            # Reiniciar estado para nuevos comandos post-LOGOUT
            if current_user is None and command not in ["LOGIN", "REGISTER"]:
                conn.sendall(b"NEED_LOGIN\n")
                continue

            if command == "REGISTER":
                try:
                    print("[SERVER] Procesando registro")
                    conn.sendall(b"READY\n")
                    
                    data = conn.recv(1024).decode().strip().split('\n')
                    if len(data) != 2:
                        conn.sendall(b'REGISTER_FAILED: Formato invalido\n')
                        continue
                        
                    username, password = data
                    
                    if register_user(username, password):
                        conn.sendall(b'REGISTER_SUCCESS\n')
                        log_event("REGISTER_SUCCESS", username)
                    else:
                        conn.sendall(b'REGISTER_FAILED: Usuario ya existe o error en BD\n')
                        log_event("REGISTER_FAILED", details=username)
                        
                except Exception as e:
                    print(f"[SERVER] Error en registro: {str(e)}")
                    conn.sendall(b'REGISTER_ERROR\n')

            elif command == "LOGIN":
                try:
                    print("[SERVER] Procesando login")
                    conn.sendall(b"READY\n")
                    
                    credentials = conn.recv(1024).decode().strip().split('\n')
                    if len(credentials) != 2:
                        conn.sendall(b"LOGIN_FAILED: Formato invalido\n")
                        continue
                        
                    username, password = credentials
                    print(f"[SERVER] Verificando credenciales para {username}")
                    
                    if verify_user(username, password):
                        conn.sendall(b"LOGIN_SUCCESS\n")
                        current_user = username
                        print(f"[SERVER] Autenticación exitosa para {username}")
                        log_event("LOGIN_SUCCESS", username)
                    else:
                        conn.sendall(b"LOGIN_FAILED: Credenciales incorrectas\n")
                        print(f"[SERVER] Autenticación fallida para {username}")
                        log_event("LOGIN_FAILED", username)
                        
                except Exception as e:
                    print(f"[SERVER] Error en login: {str(e)}")
                    conn.sendall(b"LOGIN_ERROR\n")

            elif command == "SEND":
                if current_user is None:
                    conn.sendall(b'NEED_LOGIN\n')
                    print(f"[SERVER] Intento de SEND sin autenticación desde {addr}")
                    continue
                    
                try:
                    print(f"[SERVER] Procesando SEND para {current_user}")
                    
                    # Paso 1: Confirmar READY
                    conn.sendall(b'READY\n')
                    
                    # Paso 2: Recibir destinatario y mensaje
                    data = conn.recv(4096).decode().strip().split('\n')
                    if len(data) < 2:
                        conn.sendall(b'MESSAGE_FAILED: Formato invalido\n')
                        continue
                        
                    recipient = data[0]
                    message = '\n'.join(data[1:])  # Permite mensajes multilínea
                    
                    print(f"[SERVER] Mensaje de {current_user} para {recipient}")
                    
                    # Procesar mensaje
                    if send_message(current_user, recipient, message):
                        conn.sendall(b'MESSAGE_SENT\n')
                        print(f"[SERVER] Mensaje entregado")
                    else:
                        conn.sendall(b'MESSAGE_FAILED\n')
                        print(f"[SERVER] Falló el envío")
                        
                except Exception as e:
                    print(f"[SERVER] Error en SEND: {str(e)}")
                    try:
                        conn.sendall(b'MESSAGE_ERROR\n')
                    except:
                        pass

            elif command == "GET":
                if current_user is None:
                    conn.sendall(b"NEED_LOGIN\n")
                    continue
                    
                try:
                    print(f"[SERVER] Procesando GET para {current_user}")
                    messages = get_messages(current_user)
                    
                    # Enviar cantidad de mensajes
                    conn.sendall(str(len(messages)).encode() + b"\n")
                    
                    # Esperar confirmación READY
                    ready = conn.recv(1024).decode().strip()
                    if ready != "READY":
                        raise ConnectionError(f"Se esperaba READY, se recibió: {ready}")
                    
                    # Enviar cada mensaje
                    for msg in messages:
                        formatted = f"{msg['sender']}|{msg['message']}|{msg['time']}"
                        conn.sendall(formatted.encode() + b"\n")
                        
                        # Esperar ACK
                        ack = conn.recv(3).decode().strip()
                        if ack != "ACK":
                            raise ConnectionError("Falta confirmación ACK")
                            
                    print(f"[SERVER] Mensajes enviados a {current_user}")
                    
                except Exception as e:
                    print(f"[ERROR] Error al enviar mensajes: {str(e)}")
                    conn.sendall(b"ERROR\n")

            elif command == "LOGOUT":
                try:
                    if current_user:
                        print(f"[SERVER] Procesando logout para {current_user}")
                        log_event("USER_LOGOUT", current_user)
                        
                        current_user = None
                        conn.sendall(b"LOGOUT_SUCCESS\n")
                        print(f"[SERVER] Sesión cerrada correctamente")
                    else:
                        conn.sendall(b"LOGOUT_FAILED: No hay sesion activa\n")
                        
                except Exception as e:
                    print(f"[SERVER] Error en logout: {str(e)}")
                    try:
                        conn.sendall(b"LOGOUT_FAILED\n")
                    except:
                        pass

            elif command == "EXIT":
                log_event("CONNECTION_CLOSED", current_user)
                break
                
            else:
                conn.sendall(b'INVALID_COMMAND\n')
                log_event("INVALID_COMMAND", current_user, details=command)
                
    except Exception as e:
        log_event("CONNECTION_ERROR", current_user, str(e))
    finally:
        conn.close()
        print(f"[SERVER] Conexión cerrada con {addr}")

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