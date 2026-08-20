import tkinter as tk
from tkinter import messagebox

from auth_controller import InventoryAuthController


class LoginWindow:
    def __init__(self, root, app_manager):
        self.root = root
        self.app_manager = app_manager
        self.controller = InventoryAuthController()
        self.root.title("Secure Inventory System - Authentication")
        self.root.geometry("460x500")
        self.root.minsize(460, 500)
        self.root.resizable(False, False)
        self.login_frame = tk.Frame(root)
        self.register_frame = tk.Frame(root)
        self.reset_frame = tk.Frame(root)
        self.build_login_view()
        self.build_register_view()
        self.build_reset_view()
        self.show_login_view()

    def _field(self, parent, label, show=None):
        row = tk.Frame(parent)
        row.pack(fill="x", padx=24, pady=5)
        row.columnconfigure(1, weight=1)
        tk.Label(row, text=label, width=14, anchor="w", font=("Arial", 11)).grid(row=0, column=0, padx=(0, 12), sticky="w")
        entry = tk.Entry(row, width=32, font=("Arial", 12), show=show) if show else tk.Entry(row, width=32, font=("Arial", 12))
        entry.grid(row=0, column=1, sticky="ew")
        return entry

    def _password_toggle(self, parent, entry):
        visible = tk.BooleanVar(value=False)
        tk.Checkbutton(
            parent,
            text="Show Password",
            variable=visible,
            command=lambda: entry.config(show="" if visible.get() else "*"),
        ).pack(anchor="w", padx=122, pady=(0, 5))

    def build_login_view(self):
        tk.Label(self.login_frame, text="Campus Hardware Inventory Security Login", font=("Arial", 20, "bold")).pack(pady=(32, 22))
        self.entry_user = self._field(self.login_frame, "Username")
        self.entry_pass = self._field(self.login_frame, "Password", "*")
        self._password_toggle(self.login_frame, self.entry_pass)
        buttons = tk.Frame(self.login_frame)
        buttons.pack(pady=8)
        tk.Button(buttons, text="Login", width=13, height=1, font=("Arial", 12, "bold"), command=self.handle_login, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(buttons, text="Register", width=13, height=1, font=("Arial", 12, "bold"), command=self.show_register_view, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(self.login_frame, text="Reset / Unlock Password", command=self.show_reset_view, width=27, height=1, font=("Arial", 12)).pack(pady=8)

    def build_register_view(self):
        tk.Label(self.register_frame, text="Create Account", font=("Arial", 18, "bold")).pack(pady=(32, 22))
        self.reg_entry_user = self._field(self.register_frame, "Username")
        self.reg_entry_email = self._field(self.register_frame, "Email")
        self.reg_entry_pass = self._field(self.register_frame, "Password", "*")
        self._password_toggle(self.register_frame, self.reg_entry_pass)
        tk.Label(self.register_frame, text="Role").pack(anchor="w", padx=28)
        self.reg_role = tk.StringVar(value="USER")
        tk.OptionMenu(self.register_frame, self.reg_role, "USER", "ADMIN").pack(anchor="w", padx=28, pady=(0, 14))
        buttons = tk.Frame(self.register_frame)
        buttons.pack()
        tk.Button(buttons, text="Register", width=13, height=1, font=("Arial", 11, "bold"), command=self.handle_register, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(buttons, text="Back to Login", width=13, height=1, font=("Arial", 11), command=self.show_login_view).pack(side=tk.LEFT, padx=5)

    def build_reset_view(self):
        tk.Label(self.reset_frame, text="Reset / Unlock Password", font=("Arial", 18, "bold")).pack(pady=(32, 22))
        tk.Label(self.reset_frame, text="Submit your registered email for admin approval.", wraplength=350).pack(pady=(0, 10))
        self.reset_email = self._field(self.reset_frame, "Registered Email")
        self.reset_user = self._field(self.reset_frame, "Username")
        self.reset_pass = self._field(self.reset_frame, "New Password", "*")
        self._password_toggle(self.reset_frame, self.reset_pass)
        tk.Button(self.reset_frame, text="Submit Reset Request", command=self.handle_reset_request, width=25, height=1, font=("Arial", 11), bg="#f0ad4e").pack(pady=5)
        tk.Button(self.reset_frame, text="Complete Approved Reset", command=self.handle_reset_password, width=25, height=1, font=("Arial", 11), bg="#5cb85c", fg="white").pack(pady=5)
        tk.Button(self.reset_frame, text="Back to Login", command=self.show_login_view, width=25, height=1, font=("Arial", 11)).pack(pady=5)

    def _show(self, frame):
        for view in (self.login_frame, self.register_frame, self.reset_frame):
            view.pack_forget()
        frame.pack(fill="both", expand=True)

    def show_login_view(self):
        self._show(self.login_frame)

    def show_register_view(self):
        self._show(self.register_frame)

    def show_reset_view(self):
        self._show(self.reset_frame)

    def handle_login(self):
        username, password = self.entry_user.get().strip(), self.entry_pass.get()
        success, message = self.controller.login_user(username, password)
        if success:
            self.app_manager.current_user = self.controller.get_user(username)
            self.app_manager.show_main()
        else:
            messagebox.showerror("Login Failed", message)

    def handle_register(self):
        success, message = self.controller.register_user(self.reg_entry_user.get(), self.reg_entry_pass.get(), self.reg_entry_email.get(), self.reg_role.get())
        (messagebox.showinfo if success else messagebox.showerror)("Registration", message)
        if success:
            self.show_login_view()

    def handle_reset_request(self):
        success, message = self.controller.request_password_reset(self.reset_email.get())
        (messagebox.showinfo if success else messagebox.showerror)("Password Reset", message)

    def handle_reset_password(self):
        success, message = self.controller.reset_password(self.reset_user.get().strip(), self.reset_pass.get())
        (messagebox.showinfo if success else messagebox.showerror)("Password Reset", message)
        if success:
            self.show_login_view()
