import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from PIL import Image, ImageTk
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from client.core.auth import AuthManager
from client.core.network import NetworkClient

class ChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat App")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Configuración de estilos
        self.setup_styles()
        
        # Componentes de la aplicación
        self.network = NetworkClient()
        self.auth = AuthManager(self.network)
        self.current_user = None
        
        # Mostrar pantalla de inicio
        self.show_login_screen()
        
    def setup_styles(self):
        """Configura los estilos visuales de la aplicación"""
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        self.style.configure('TButton', font=('Arial', 10), padding=5)
        self.style.configure('TEntry', font=('Arial', 10), padding=5)
        self.style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        
    def clear_frame(self):
        """Limpia el frame actual"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def show_login_screen(self):
        """Muestra la pantalla de inicio de sesión"""
        self.clear_frame()
        
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=50)
        
        # Título
        ttk.Label(main_frame, text="Chat App", style='Title.TLabel').pack(pady=20)
        
        # Frame de formulario
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(pady=20)
        
        # Campos de entrada
        ttk.Label(form_frame, text="Usuario:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_entry = ttk.Entry(form_frame)
        self.username_entry.grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text="Contraseña:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_entry = ttk.Entry(form_frame, show="*")
        self.password_entry.grid(row=1, column=1, pady=5, padx=5)
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Iniciar Sesión", command=self.handle_login).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Registrarse", command=self.show_register_screen).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Conectar", command=self.connect_to_server).pack(side=tk.LEFT, padx=10)
        
    def show_register_screen(self):
        """Muestra la pantalla de registro"""
        self.clear_frame()
        
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=50)
        
        # Título
        ttk.Label(main_frame, text="Registro", style='Title.TLabel').pack(pady=20)
        
        # Frame de formulario
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(pady=20)
        
        # Campos de entrada
        ttk.Label(form_frame, text="Usuario:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.reg_username_entry = ttk.Entry(form_frame)
        self.reg_username_entry.grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text="Contraseña:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.reg_password_entry = ttk.Entry(form_frame, show="*")
        self.reg_password_entry.grid(row=1, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text="Confirmar Contraseña:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.reg_confirm_entry = ttk.Entry(form_frame, show="*")
        self.reg_confirm_entry.grid(row=2, column=1, pady=5, padx=5)
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Registrarse", command=self.handle_register).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Volver", command=self.show_login_screen).pack(side=tk.LEFT, padx=10)
    
    def show_chat_screen(self):
        """Muestra la pantalla principal del chat"""
        self.clear_frame()
        
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Barra superior
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(top_frame, text=f"Usuario: {self.current_user}", style='Title.TLabel').pack(side=tk.LEFT)
        ttk.Button(top_frame, text="Cerrar Sesión", command=self.handle_logout).pack(side=tk.RIGHT)
        
        # Área de mensajes
        self.message_area = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            width=60,
            height=20,
            font=('Arial', 10)
        )
        self.message_area.pack(expand=True, fill=tk.BOTH, pady=10)
        self.message_area.config(state=tk.DISABLED)
        
        # Frame de envío
        send_frame = ttk.Frame(main_frame)
        send_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(send_frame, text="Destinatario:").pack(side=tk.LEFT)
        self.recipient_entry = ttk.Entry(send_frame, width=15)
        self.recipient_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(send_frame, text="Mensaje:").pack(side=tk.LEFT)
        self.message_entry = ttk.Entry(send_frame)
        self.message_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        
        ttk.Button(send_frame, text="Enviar", command=self.send_message).pack(side=tk.LEFT, padx=5)
        ttk.Button(send_frame, text="Actualizar", command=self.refresh_messages).pack(side=tk.LEFT)
    
    # Métodos para manejar la lógica de la aplicación
    def connect_to_server(self):
        """Conecta al servidor"""
        try:
            if self.network.connect():
                messagebox.showinfo("Conexión", "Conectado al servidor exitosamente")
            else:
                messagebox.showerror("Error", "No se pudo conectar al servidor")
        except Exception as e:
            messagebox.showerror("Error", f"Error de conexión: {str(e)}")
    
    def handle_login(self):
        """Maneja el inicio de sesión"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showwarning("Advertencia", "Usuario y contraseña son requeridos")
            return
            
        try:
            if self.auth.login(username, password):
                self.current_user = username
                self.show_chat_screen()
                self.refresh_messages()
            else:
                messagebox.showerror("Error", "Credenciales incorrectas")
        except Exception as e:
            messagebox.showerror("Error", f"Error al iniciar sesión: {str(e)}")
    
    def handle_register(self):
        """Maneja el registro de usuario"""
        username = self.reg_username_entry.get()
        password = self.reg_password_entry.get()
        confirm = self.reg_confirm_entry.get()
        
        if not username or not password:
            messagebox.showwarning("Advertencia", "Todos los campos son requeridos")
            return
            
        if password != confirm:
            messagebox.showwarning("Advertencia", "Las contraseñas no coinciden")
            return
            
        try:
            if self.auth.register(username, password):
                messagebox.showinfo("Éxito", "Registro exitoso")
                self.show_login_screen()
            else:
                messagebox.showerror("Error", "El usuario ya existe o hubo un error")
        except Exception as e:
            messagebox.showerror("Error", f"Error en el registro: {str(e)}")
    
    def handle_logout(self):
        """Maneja el cierre de sesión"""
        try:
            if self.auth.logout():
                self.current_user = None
                self.show_login_screen()
            else:
                messagebox.showerror("Error", "No se pudo cerrar la sesión")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cerrar sesión: {str(e)}")
    
    def send_message(self):
        """Envía un mensaje"""
        recipient = self.recipient_entry.get()
        message = self.message_entry.get()
        
        if not recipient or not message:
            messagebox.showwarning("Advertencia", "Destinatario y mensaje son requeridos")
            return
            
        try:
            if self.network.send_message(recipient, message):
                self.message_entry.delete(0, tk.END)
                self.refresh_messages()
            else:
                messagebox.showerror("Error", "No se pudo enviar el mensaje")
        except Exception as e:
            messagebox.showerror("Error", f"Error al enviar mensaje: {str(e)}")
    
    def refresh_messages(self):
        """Actualiza los mensajes recibidos"""
        try:
            messages = self.network.get_messages()
            self.message_area.config(state=tk.NORMAL)
            self.message_area.delete(1.0, tk.END)
            
            if not messages:
                self.message_area.insert(tk.END, "No hay mensajes nuevos\n")
            else:
                for msg in messages:
                    self.message_area.insert(tk.END, 
                        f"[{msg['time']}] {msg['sender']}:\n{msg['message']}\n\n")
                    self.message_area.insert(tk.END, "-"*50 + "\n")
            
            self.message_area.config(state=tk.DISABLED)
            self.message_area.see(tk.END)
        except Exception as e:
            messagebox.showerror("Error", f"Error al obtener mensajes: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatGUI(root)
    root.mainloop()