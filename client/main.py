import socket
from server.auth import hash_password
from server.encryption import encrypt_message, decrypt_message

HOST = '192.168.1.100'  # IP del servidor
PORT = 65432

def login(s):
    username = input("Usuario: ")
    password = input("Contraseña: ")
    s.sendall(username.encode())
    s.sendall(password.encode())
    response = s.recv(1024)
    return response == b'AUTH_SUCCESS'

def send_messages(s):
    while True:
        message = input("> ")
        if message.lower() == 'exit':
            break
        encrypted = encrypt_message(message)
        s.sendall(encrypted)

def start_client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        if login(s):
            print("Autenticación exitosa")
            send_messages(s)
        else:
            print("Error de autenticación")

if __name__ == "__main__":
    start_client()