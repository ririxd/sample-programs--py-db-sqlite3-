import tkinter as tk
from tkinter import messagebox
from auth_controller import AuthController

class LoginWindow:
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.auth = AuthController()

        self.root.title("System Auth - Login")
        self.root.geometry("320x200")
        self.root.resizable(False, False)

        tk.Label(root, text="Username:").pack(anchor="w", padx=20, pady=(15, 0))
        self.entry_user = tk.Entry(root, width=34)
        self.entry_user.pack(padx=20)

        tk.Label(root, text="Password:").pack(anchor="w", padx=20, pady=(10, 0))
        self.entry_pass = tk.Entry(root, show="*", width=34)
        self.entry_pass.pack(padx=20, pady=(0, 15))

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Login", command=self.handle_login, bg="#4CAF50", fg="white", width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Register", command=self.handle_register, bg="#2196F3", fg="white", width=12).pack(side=tk.LEFT, padx=5)

    def handle_login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()

        success, msg = self.auth.login(username, password)
        if success:
            messagebox.showinfo("Login Successful", msg)
            if callable(self.on_login_success):
                self.on_login_success()
        else:
            messagebox.showerror("Login Failed", msg)

    def handle_register(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()

        success, msg = self.auth.register(username, password)
        if success:
            messagebox.showinfo("Registration Successful", msg)
        else:
            messagebox.showerror("Registration Alert", msg)