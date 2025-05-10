import logging
import platform
import os
from typing import Optional
from getpass import getpass

logger = logging.getLogger(__name__)

class CLInterface:
    def __init__(self, auth_manager, network_client):
        self.auth = auth_manager
        self.network = network_client
    
    def clear_screen(self):
        """Limpia la pantalla de la consola de manera multiplataforma"""
        if platform.system() == "Windows":
            os.system('cls')
        else:
            os.system('clear')

    def show_main_menu(self):
        """Muestra el menú principal"""
        while True:
            self.clear_screen()
            print("\n--- MENÚ PRINCIPAL ---")
            print("1. Conectar al servidor")
            print("2. Registrarse")
            print("3. Iniciar sesión")
            print("4. Salir\n")
            
            choice = input("Seleccione una opción: ")
            
            if choice == "1":
                self.connect_to_server()
            elif choice == "2":
                self.register_flow()
            elif choice == "3":
                self.login_flow()
            elif choice == "4":
                print("Saliendo...")
                return
            else:
                print("Opción inválida, intente nuevamente")

    def connect_to_server(self):
        """Flujo de conexión al servidor"""
        self.clear_screen()
        if self.network.connected:
            print("Ya estás conectado al servidor")
            return
            
        print("\n--- CONEXIÓN AL SERVIDOR ---")
        if self.network.connect():
            print("Conexión exitosa")
        else:
            print("No se pudo conectar al servidor")

    def register_flow(self):
        """Flujo de registro de usuario"""
        self.clear_screen()
        if not self.network.connected:
            print("Primero debes conectarte al servidor")
            return
            
        print("\n--- REGISTRO DE USUARIO ---")
        username = input("Nombre de usuario: ").strip()
        password = getpass("Contraseña: ").strip()
        
        if self.auth.register(username, password):
            print("Registro exitoso")
        else:
            print("Error en el registro")

    def login_flow(self):
        """Flujo de inicio de sesión"""
        self.clear_screen()
        if not self.network.connected:
            print("Primero debes conectarte al servidor")
            return
            
        print("\n--- INICIO DE SESIÓN ---")
        username = input("Usuario: ").strip()
        password = getpass("Contraseña: ").strip()
        
        if self.auth.login(username, password):
            print("Autenticación exitosa")
            self.show_chat_menu()
        else:
            print("Error de autenticación")

    def show_chat_menu(self):
        """Muestra el menú de chat después de login"""
        while True:
            self.clear_screen()
            print("\n--- MENÚ DE CHAT ---")
            print("1. Enviar mensaje")
            print("2. Ver mensajes nuevos")
            print("3. Cerrar sesión")
            
            choice = input("Seleccione una opción: ")
            
            if choice == "1":
                self.send_message_flow()
            elif choice == "2":
                self.show_messages_flow()
            elif choice == "3":
                if self.auth.logout():
                    print("Sesión cerrada")
                    return
                else:
                    print("Error al cerrar sesión")
            else:
                print("Opción inválida")

    def send_message_flow(self):
        """Flujo para enviar mensajes"""
        self.clear_screen()
        print("\n--- ENVIAR MENSAJE ---")
        recipient = input("Destinatario: ").strip()
        message = input("Mensaje: ").strip()
        
        if self.network.send_message(recipient, message):
            print("Mensaje enviado")
        else:
            print("Error al enviar mensaje")

    def show_messages_flow(self):
        """Muestra todos los mensajes recibidos"""
        self.clear_screen()
        try:
            # Verificar conexión antes de empezar
            if not self.network.connected:
                print("\nError: No hay conexión con el servidor")
                input("Presione Enter para continuar...")
                return
                
            print("\nObteniendo mensajes...")
            
            # Obtener mensajes con reintentos
            messages = []
            for attempt in range(3):
                try:
                    messages = self.network.get_messages()
                    break
                except Exception as e:
                    if attempt == 2:
                        print(f"\nError al obtener mensajes: {str(e)}")
                        input("Presione Enter para continuar...")
                        return
            
            if not messages:
                print("\nNo hay mensajes nuevos")
                input("Presione Enter para continuar...")
                return
                
            # Mostrar mensajes
            print(f"\n--- MENSAJES RECIBIDOS ({len(messages)}) ---")
            for idx, msg in enumerate(messages, 1):
                print(f"\n[{idx}] {msg['time']} - De: {msg['sender']}")
                print(f"   {msg['message']}")
                print("-" * 40)
            
            input("\nPresione Enter para volver al menú...")
            
        except Exception as e:
            print(f"\nError inesperado: {str(e)}")
            input("Presione Enter para continuar...")
        